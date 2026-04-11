from __future__ import annotations

from typing import Any, Protocol, TypeVar

from collections.abc import Iterable

import httpx
from pydantic import BaseModel, ConfigDict

from spotifyify.exceptions import SpotifyAPIError

TModel = TypeVar("TModel", bound=BaseModel)
JSONPrimitive = str | int | float | bool | None
JSONValue = JSONPrimitive | dict[str, "JSONValue"] | list["JSONValue"]
JSONResponse = dict[str, JSONValue] | list[JSONValue] | None


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


class AsyncHttpClient:
    def __init__(self, *, base_url: str | None = None, timeout: float = 10.0) -> None:
        self._client = (
            httpx.AsyncClient(base_url=base_url, timeout=timeout)
            if base_url
            else httpx.AsyncClient(timeout=timeout)
        )

    async def __aenter__(self) -> AsyncHttpClient:
        return self

    async def __aexit__(self, exc_type, exc, tb) -> None:
        await self.close()

    async def close(self) -> None:
        await self._client.aclose()

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

    @staticmethod
    def _validate_response(
        parsed: JSONResponse,
        response_model: type[TModel] | None,
    ) -> TModel | JSONResponse:
        if response_model is None or parsed is None:
            return parsed
        if isinstance(parsed, list):
            raise SpotifyAPIError(500, "Expected object response but got list")
        return response_model.model_validate(parsed)

    async def request_json(
        self,
        method: str,
        url: str,
        *,
        params: QueryParams | BaseModel | dict[str, Any] | None = None,
        payload: RequestPayload
        | BaseModel
        | dict[str, Any]
        | list[Any]
        | str
        | None = None,
        headers: dict[str, str] | None = None,
        response_model: type[TModel] | None = None,
    ) -> TModel | JSONResponse:
        response = await self._client.request(
            method,
            url,
            headers=headers,
            params=self._dump_params(params),
            json=self._dump_payload(payload),
        )
        parsed = self._parse_response(response)
        return self._validate_response(parsed, response_model)

    async def get(
        self,
        url: str,
        *,
        params: QueryParams | BaseModel | dict[str, Any] | None = None,
        headers: dict[str, str] | None = None,
        response_model: type[TModel] | None = None,
    ) -> TModel | JSONResponse:
        return await self.request_json(
            "GET", url, params=params, headers=headers, response_model=response_model
        )

    async def post(
        self,
        url: str,
        *,
        params: QueryParams | BaseModel | dict[str, Any] | None = None,
        payload: RequestPayload
        | BaseModel
        | dict[str, Any]
        | list[Any]
        | str
        | None = None,
        headers: dict[str, str] | None = None,
        response_model: type[TModel] | None = None,
    ) -> TModel | JSONResponse:
        return await self.request_json(
            "POST",
            url,
            params=params,
            payload=payload,
            headers=headers,
            response_model=response_model,
        )

    async def put(
        self,
        url: str,
        *,
        params: QueryParams | BaseModel | dict[str, Any] | None = None,
        payload: RequestPayload
        | BaseModel
        | dict[str, Any]
        | list[Any]
        | str
        | None = None,
        headers: dict[str, str] | None = None,
        response_model: type[TModel] | None = None,
    ) -> TModel | JSONResponse:
        return await self.request_json(
            "PUT",
            url,
            params=params,
            payload=payload,
            headers=headers,
            response_model=response_model,
        )

    async def patch(
        self,
        url: str,
        *,
        params: QueryParams | BaseModel | dict[str, Any] | None = None,
        payload: RequestPayload
        | BaseModel
        | dict[str, Any]
        | list[Any]
        | str
        | None = None,
        headers: dict[str, str] | None = None,
        response_model: type[TModel] | None = None,
    ) -> TModel | JSONResponse:
        return await self.request_json(
            "PATCH",
            url,
            params=params,
            payload=payload,
            headers=headers,
            response_model=response_model,
        )

    async def delete(
        self,
        url: str,
        *,
        params: QueryParams | BaseModel | dict[str, Any] | None = None,
        payload: RequestPayload
        | BaseModel
        | dict[str, Any]
        | list[Any]
        | str
        | None = None,
        headers: dict[str, str] | None = None,
        response_model: type[TModel] | None = None,
    ) -> TModel | JSONResponse:
        return await self.request_json(
            "DELETE",
            url,
            params=params,
            payload=payload,
            headers=headers,
            response_model=response_model,
        )

    async def post_form(
        self,
        url: str,
        *,
        data: BaseModel | dict[str, Any],
        headers: dict[str, str] | None = None,
        response_model: type[TModel] | None = None,
    ) -> TModel | dict[str, Any]:
        form_data = (
            data.model_dump(mode="json", exclude_none=True)
            if isinstance(data, BaseModel)
            else data
        )
        response = await self._client.post(url, data=form_data, headers=headers)
        parsed = self._parse_response(response)
        if not isinstance(parsed, dict):
            raise SpotifyAPIError(
                response.status_code, "Unexpected non-object response body"
            )
        if response_model is None:
            return parsed
        return response_model.model_validate(parsed)

    @staticmethod
    def _parse_response(response: httpx.Response) -> JSONResponse:
        if response.status_code == 204:
            return None

        if response.status_code >= 400:
            try:
                data = response.json()
                err = data.get("error", data) if isinstance(data, dict) else data
                message = (
                    err.get("message", response.text)
                    if isinstance(err, dict)
                    else str(err)
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


class SpotifyAPIHttpClient:
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
        self._http = AsyncHttpClient(base_url=base_url, timeout=timeout)

    async def __aenter__(self) -> SpotifyAPIHttpClient:
        return self

    async def __aexit__(self, exc_type, exc, tb) -> None:
        await self.close()

    async def close(self) -> None:
        await self._http.close()

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
        require_user: bool = True,
        response_model: type[TModel] | None = None,
    ) -> TModel | JSONResponse:
        token = await self._token_provider.get_access_token(
            require_user=require_user,
            scope=self._scopes,
        )
        headers = {"Authorization": f"Bearer {token}"}
        return await self._http.request_json(
            method,
            path,
            params=params,
            payload=payload,
            headers=headers,
            response_model=response_model,
        )

    async def get(
        self,
        path: str,
        *,
        params: QueryParams | BaseModel | dict[str, Any] | None = None,
        require_user: bool = True,
        response_model: type[TModel] | None = None,
    ) -> TModel | JSONResponse:
        return await self.request_json(
            "GET",
            path,
            params=params,
            require_user=require_user,
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
        require_user: bool = True,
        response_model: type[TModel] | None = None,
    ) -> TModel | JSONResponse:
        return await self.request_json(
            "POST",
            path,
            params=params,
            payload=payload,
            require_user=require_user,
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
        require_user: bool = True,
        response_model: type[TModel] | None = None,
    ) -> TModel | JSONResponse:
        return await self.request_json(
            "PUT",
            path,
            params=params,
            payload=payload,
            require_user=require_user,
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
        require_user: bool = True,
        response_model: type[TModel] | None = None,
    ) -> TModel | JSONResponse:
        return await self.request_json(
            "PATCH",
            path,
            params=params,
            payload=payload,
            require_user=require_user,
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
        require_user: bool = True,
        response_model: type[TModel] | None = None,
    ) -> TModel | JSONResponse:
        return await self.request_json(
            "DELETE",
            path,
            params=params,
            payload=payload,
            require_user=require_user,
            response_model=response_model,
        )
