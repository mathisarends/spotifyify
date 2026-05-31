import asyncio
from enum import StrEnum
from typing import Any, Protocol, Self

from collections.abc import Iterable

import httpx
from pydantic import BaseModel, ConfigDict

from spotifyify.exceptions import SpotifyAPIError

_DEFAULT_MAX_RETRIES = 3
_DEFAULT_RETRY_BACKOFF_SECONDS = 1.0
_RETRYABLE_SERVER_ERROR_STATUS_CODES = frozenset({500, 502, 503, 504})


class _HttpMethod(StrEnum):
    GET = "GET"
    POST = "POST"
    PUT = "PUT"
    PATCH = "PATCH"
    DELETE = "DELETE"
    HEAD = "HEAD"
    OPTIONS = "OPTIONS"


_IDEMPOTENT_METHODS = frozenset(
    {
        _HttpMethod.GET,
        _HttpMethod.PUT,
        _HttpMethod.DELETE,
        _HttpMethod.HEAD,
        _HttpMethod.OPTIONS,
    }
)


class QueryParams(BaseModel):
    model_config = ConfigDict(extra="allow")


_JsonPayload = BaseModel | dict[str, Any] | list[Any] | str | None
_SerializedJsonPayload = dict[str, Any] | list[Any] | str | None


class AccessTokenProvider(Protocol):
    async def get_access_token(
        self,
        require_user: bool,
        scope: str | list[str] | tuple[str, ...] | None = None,
    ) -> str: ...


def parse_response(response: httpx.Response) -> dict[str, Any] | list[Any] | None:
    if response.status_code == 204:
        return None

    if response.status_code >= 400:
        try:
            data = response.json()
            err = data.get("error", data) if isinstance(data, dict) else data
            message = (
                err.get("message", response.text) if isinstance(err, dict) else str(err)
            )
        except ValueError:
            data = None
            message = response.text
        raise SpotifyAPIError(
            response.status_code,
            message,
            data if isinstance(data, dict) else None,
        )

    if not response.content:
        return None

    return response.json()


class SpotifyClient:
    def __init__(
        self,
        token_provider: AccessTokenProvider,
        scopes: Iterable[str] | None,
        *,
        base_url: str,
        timeout: float = 10.0,
        max_retries: int = _DEFAULT_MAX_RETRIES,
        retry_backoff_seconds: float = _DEFAULT_RETRY_BACKOFF_SECONDS,
    ) -> None:
        if max_retries < 0:
            raise ValueError("max_retries must be greater than or equal to 0")
        if retry_backoff_seconds < 0:
            raise ValueError("retry_backoff_seconds must be greater than or equal to 0")
        self._token_provider = token_provider
        self._scopes = list(scopes or [])
        self._base_url = base_url
        self._timeout = timeout
        self._max_retries = max_retries
        self._retry_backoff_seconds = retry_backoff_seconds
        self._client: httpx.AsyncClient | None = None

    async def open(self) -> None:
        if self._client is None:
            self._client = httpx.AsyncClient(
                base_url=self._base_url, timeout=self._timeout
            )

    async def __aenter__(self) -> Self:
        return self

    async def __aexit__(self, exc_type, exc, tb) -> None:
        await self.close()

    async def close(self) -> None:
        if self._client is None:
            return
        await self._client.aclose()
        self._client = None

    @staticmethod
    def _dump_params(
        params: QueryParams | BaseModel | dict[str, Any] | None,
    ) -> dict[str, Any] | None:
        if params is None:
            return None
        if isinstance(params, BaseModel):
            return params.model_dump(mode="json", exclude_none=True)
        return QueryParams.model_validate(params).model_dump(
            mode="json", exclude_none=True
        )

    @staticmethod
    def _dump_payload(payload: _JsonPayload) -> _SerializedJsonPayload:
        if isinstance(payload, BaseModel):
            return payload.model_dump(mode="json", exclude_none=True)
        return payload

    @staticmethod
    def _should_retry(method: _HttpMethod, status_code: int) -> bool:
        if status_code == 429:
            return True
        return (
            method in _IDEMPOTENT_METHODS
            and status_code in _RETRYABLE_SERVER_ERROR_STATUS_CODES
        )

    def _retry_delay(self, response: httpx.Response, attempt: int) -> float:
        retry_after = response.headers.get("Retry-After")
        if retry_after is not None:
            try:
                return max(0.0, float(retry_after))
            except ValueError:
                pass
        return self._retry_backoff_seconds * (2**attempt)

    async def _request_json(
        self,
        method: _HttpMethod,
        path: str,
        *,
        params: QueryParams | BaseModel | dict[str, Any] | None = None,
        payload: _JsonPayload = None,
        content: str | bytes | None = None,
        require_user: bool = True,
        headers: dict[str, str] | None = None,
        response_model: type[BaseModel] | None = None,
    ) -> Any:
        await self.open()
        token = await self._token_provider.get_access_token(
            require_user=require_user,
            scope=self._scopes,
        )
        request_headers = {"Authorization": f"Bearer {token}"}
        if headers:
            request_headers.update(headers)
        if self._client is None:
            raise RuntimeError("HTTP client was not initialized")

        json_payload = None if content is not None else self._dump_payload(payload)
        request_params = self._dump_params(params)
        for attempt in range(self._max_retries + 1):
            response = await self._client.request(
                method.value,
                path,
                headers=request_headers,
                params=request_params,
                json=json_payload,
                content=content,
            )
            if attempt == self._max_retries or not self._should_retry(
                method, response.status_code
            ):
                break
            await asyncio.sleep(self._retry_delay(response, attempt))

        parsed = parse_response(response)

        if response_model is None or parsed is None:
            return parsed
        if isinstance(parsed, list):
            raise SpotifyAPIError(500, "Expected object response but got list")
        return response_model.model_validate(parsed)

    async def get(
        self,
        path: str,
        *,
        params: QueryParams | BaseModel | dict[str, Any] | None = None,
        require_user: bool = True,
        headers: dict[str, str] | None = None,
        response_model: type[BaseModel] | None = None,
    ) -> Any:
        return await self._request_json(
            _HttpMethod.GET,
            path,
            params=params,
            require_user=require_user,
            headers=headers,
            response_model=response_model,
        )

    async def post(
        self,
        path: str,
        *,
        params: QueryParams | BaseModel | dict[str, Any] | None = None,
        payload: _JsonPayload = None,
        content: str | bytes | None = None,
        require_user: bool = True,
        headers: dict[str, str] | None = None,
        response_model: type[BaseModel] | None = None,
    ) -> Any:
        return await self._request_json(
            _HttpMethod.POST,
            path,
            params=params,
            payload=payload,
            content=content,
            require_user=require_user,
            headers=headers,
            response_model=response_model,
        )

    async def put(
        self,
        path: str,
        *,
        params: QueryParams | BaseModel | dict[str, Any] | None = None,
        payload: _JsonPayload = None,
        content: str | bytes | None = None,
        require_user: bool = True,
        headers: dict[str, str] | None = None,
        response_model: type[BaseModel] | None = None,
    ) -> Any:
        return await self._request_json(
            _HttpMethod.PUT,
            path,
            params=params,
            payload=payload,
            content=content,
            require_user=require_user,
            headers=headers,
            response_model=response_model,
        )

    async def patch(
        self,
        path: str,
        *,
        params: QueryParams | BaseModel | dict[str, Any] | None = None,
        payload: _JsonPayload = None,
        content: str | bytes | None = None,
        require_user: bool = True,
        headers: dict[str, str] | None = None,
        response_model: type[BaseModel] | None = None,
    ) -> Any:
        return await self._request_json(
            _HttpMethod.PATCH,
            path,
            params=params,
            payload=payload,
            content=content,
            require_user=require_user,
            headers=headers,
            response_model=response_model,
        )

    async def delete(
        self,
        path: str,
        *,
        params: QueryParams | BaseModel | dict[str, Any] | None = None,
        payload: _JsonPayload = None,
        content: str | bytes | None = None,
        require_user: bool = True,
        headers: dict[str, str] | None = None,
        response_model: type[BaseModel] | None = None,
    ) -> Any:
        return await self._request_json(
            _HttpMethod.DELETE,
            path,
            params=params,
            payload=payload,
            content=content,
            require_user=require_user,
            headers=headers,
            response_model=response_model,
        )
