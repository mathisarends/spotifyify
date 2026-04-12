from typing import Any, Protocol, Self

from collections.abc import Iterable

import httpx
from pydantic import BaseModel, ConfigDict

from spotifyify.exceptions import SpotifyAPIError


class QueryParams(BaseModel):
    model_config = ConfigDict(extra="allow")


class RequestPayload(BaseModel):
    model_config = ConfigDict(extra="allow")


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
    ) -> None:
        self._token_provider = token_provider
        self._scopes = list(scopes or [])
        self._base_url = base_url
        self._timeout = timeout
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
    def _dump_payload(
        payload: RequestPayload | BaseModel | dict[str, Any] | list[Any] | str | None,
    ) -> dict[str, Any] | list[Any] | str | None:
        if payload is None:
            return None
        if isinstance(payload, BaseModel):
            return payload.model_dump(mode="json", exclude_none=True)
        if isinstance(payload, (dict, list, str)):
            return payload
        raise TypeError("payload must be a Pydantic model, dict, list, str, or None")

    async def request_json(
        self,
        method: str,
        path: str,
        *,
        params: QueryParams | BaseModel | dict[str, Any] | None = None,
        payload: RequestPayload
        | BaseModel
        | dict[str, Any]
        | list[Any]
        | str
        | None = None,
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
        response = await self._client.request(
            method,
            path,
            headers=request_headers,
            params=self._dump_params(params),
            json=json_payload,
            content=content,
        )
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
        return await self.request_json(
            "GET",
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
        payload: RequestPayload
        | BaseModel
        | dict[str, Any]
        | list[Any]
        | str
        | None = None,
        content: str | bytes | None = None,
        require_user: bool = True,
        headers: dict[str, str] | None = None,
        response_model: type[BaseModel] | None = None,
    ) -> Any:
        return await self.request_json(
            "POST",
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
        payload: RequestPayload
        | BaseModel
        | dict[str, Any]
        | list[Any]
        | str
        | None = None,
        content: str | bytes | None = None,
        require_user: bool = True,
        headers: dict[str, str] | None = None,
        response_model: type[BaseModel] | None = None,
    ) -> Any:
        return await self.request_json(
            "PUT",
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
        payload: RequestPayload
        | BaseModel
        | dict[str, Any]
        | list[Any]
        | str
        | None = None,
        content: str | bytes | None = None,
        require_user: bool = True,
        headers: dict[str, str] | None = None,
        response_model: type[BaseModel] | None = None,
    ) -> Any:
        return await self.request_json(
            "PATCH",
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
        payload: RequestPayload
        | BaseModel
        | dict[str, Any]
        | list[Any]
        | str
        | None = None,
        content: str | bytes | None = None,
        require_user: bool = True,
        headers: dict[str, str] | None = None,
        response_model: type[BaseModel] | None = None,
    ) -> Any:
        return await self.request_json(
            "DELETE",
            path,
            params=params,
            payload=payload,
            content=content,
            require_user=require_user,
            headers=headers,
            response_model=response_model,
        )
