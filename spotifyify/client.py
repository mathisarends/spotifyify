from typing import Any, Self

from collections.abc import Iterable

from pydantic import BaseModel

from spotifyify.auth import AccessTokenProvider
from spotifyify.http import (
    HttpMethod,
    HttpTransport,
    JsonPayload,
    QueryParams,
    RetryPolicy,
    dump_params,
    dump_payload,
    parse_response,
    validate_response_model,
)
from spotifyify.http.auth_context import current_access_token


class SpotifyClient:
    def __init__(
        self,
        token_provider: AccessTokenProvider,
        scopes: Iterable[str] | None,
        *,
        base_url: str,
        timeout: float = 10.0,
        max_retries: int = 3,
        retry_backoff_seconds: float = 1.0,
    ) -> None:
        self._token_provider = token_provider
        self._scopes = list(scopes or [])
        self._transport = HttpTransport(
            base_url=base_url,
            timeout=timeout,
            retry_policy=RetryPolicy(
                max_retries=max_retries,
                backoff_seconds=retry_backoff_seconds,
            ),
        )

    async def open(self) -> None:
        await self._transport.open()

    async def __aenter__(self) -> Self:
        return self

    async def __aexit__(self, exc_type, exc, tb) -> None:
        await self.close()

    async def close(self) -> None:
        await self._transport.close()

    async def _request_json(
        self,
        method: HttpMethod,
        path: str,
        *,
        params: QueryParams | BaseModel | dict[str, Any] | None = None,
        payload: JsonPayload = None,
        content: str | bytes | None = None,
        require_user: bool = True,
        headers: dict[str, str] | None = None,
        response_model: type[BaseModel] | None = None,
    ) -> Any:
        token = current_access_token.get()
        if token is None:
            token = await self._token_provider.get_access_token(
                require_user=require_user,
                scope=self._scopes,
            )
        request_headers = {"Authorization": f"Bearer {token}"}
        if headers:
            request_headers.update(headers)

        response = await self._transport.request(
            method,
            path,
            headers=request_headers,
            params=dump_params(params),
            json=None if content is not None else dump_payload(payload),
            content=content,
        )
        return validate_response_model(parse_response(response), response_model)

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
            HttpMethod.GET,
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
        payload: JsonPayload = None,
        content: str | bytes | None = None,
        require_user: bool = True,
        headers: dict[str, str] | None = None,
        response_model: type[BaseModel] | None = None,
    ) -> Any:
        return await self._request_json(
            HttpMethod.POST,
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
        payload: JsonPayload = None,
        content: str | bytes | None = None,
        require_user: bool = True,
        headers: dict[str, str] | None = None,
        response_model: type[BaseModel] | None = None,
    ) -> Any:
        return await self._request_json(
            HttpMethod.PUT,
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
        payload: JsonPayload = None,
        content: str | bytes | None = None,
        require_user: bool = True,
        headers: dict[str, str] | None = None,
        response_model: type[BaseModel] | None = None,
    ) -> Any:
        return await self._request_json(
            HttpMethod.PATCH,
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
        payload: JsonPayload = None,
        content: str | bytes | None = None,
        require_user: bool = True,
        headers: dict[str, str] | None = None,
        response_model: type[BaseModel] | None = None,
    ) -> Any:
        return await self._request_json(
            HttpMethod.DELETE,
            path,
            params=params,
            payload=payload,
            content=content,
            require_user=require_user,
            headers=headers,
            response_model=response_model,
        )
