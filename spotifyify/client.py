import math
from collections.abc import Iterable
from typing import Any, Self

import httpx
from pydantic import BaseModel

from spotifyify.auth import AccessTokenProvider
from spotifyify.config import ApiMode
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
from spotifyify.http.context import RequestContext, default_context
from spotifyify.utils import normalize_scopes
from spotifyify.validation import integer


class SpotifyAPIClient:
    def __init__(
        self,
        token_provider: AccessTokenProvider,
        scopes: Iterable[str] | str | None,
        *,
        base_url: str,
        timeout: float = 10.0,
        max_retries: int = 3,
        retry_backoff_seconds: float = 1.0,
        context: RequestContext | None = None,
        transport: httpx.AsyncBaseTransport | None = None,
        retry_policy: RetryPolicy | None = None,
        api_mode: ApiMode | str = ApiMode.DEVELOPMENT,
        concurrency: int = 8,
    ) -> None:
        self._token_provider = token_provider
        self.api_mode = ApiMode(api_mode)
        integer("concurrency", concurrency, minimum=1)
        if isinstance(timeout, bool) or not math.isfinite(timeout) or timeout <= 0:
            raise ValueError("timeout must be finite and positive")
        self.concurrency = concurrency
        self._scopes = normalize_scopes(scopes)
        self._context = context if context is not None else default_context
        self._closed = False
        self._transport = HttpTransport(
            base_url=base_url,
            timeout=timeout,
            retry_policy=retry_policy
            if retry_policy is not None
            else RetryPolicy(
                max_retries=max_retries,
                backoff_seconds=retry_backoff_seconds,
                jitter=0.1,
            ),
            context=self._context,
            transport=transport,
        )

    async def open(self) -> None:
        if self._closed:
            raise RuntimeError("Spotify client is closed; create a new instance")
        await self._transport.open()

    async def __aenter__(self) -> Self:
        return self

    async def __aexit__(self, exc_type, exc, tb) -> None:
        await self.close()

    async def close(self) -> None:
        if not self._closed:
            try:
                await self._transport.close()
            finally:
                self._closed = True

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
        retry_safe: bool | None = None,
    ) -> Any:
        if self._closed:
            raise RuntimeError("Spotify client is closed; create a new instance")
        token = self._context.access_token.get()
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
            **({"retry_safe": retry_safe} if retry_safe is not None else {}),
        )
        parsed = parse_response(
            response,
            allow_non_json=path.startswith("/me/player") and method != HttpMethod.GET,
        )
        return validate_response_model(parsed, response_model)

    async def get(
        self,
        path: str,
        *,
        params: QueryParams | BaseModel | dict[str, Any] | None = None,
        require_user: bool = True,
        headers: dict[str, str] | None = None,
        response_model: type[BaseModel] | None = None,
        retry_safe: bool | None = None,
    ) -> Any:
        return await self._request_json(
            HttpMethod.GET,
            path,
            params=params,
            require_user=require_user,
            headers=headers,
            response_model=response_model,
            retry_safe=retry_safe,
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
        retry_safe: bool | None = None,
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
            retry_safe=retry_safe,
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
        retry_safe: bool | None = None,
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
            retry_safe=retry_safe,
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
        retry_safe: bool | None = None,
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
            retry_safe=retry_safe,
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
        retry_safe: bool | None = None,
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
            retry_safe=retry_safe,
        )


# Compatibility for users importing the former low-level class by module path.
SpotifyClient = SpotifyAPIClient
