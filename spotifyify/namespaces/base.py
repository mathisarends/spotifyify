from collections.abc import Iterable
from typing import Any

from pydantic import BaseModel

from spotifyify.batching import bounded_map, chunks
from spotifyify.client import SpotifyAPIClient
from spotifyify.config import ApiMode
from spotifyify.exceptions import (
    SpotifyAPIError,
    SpotifyResponseError,
    SpotifyUnsupportedOperation,
)
from spotifyify.http.response import list_response, object_response, validate_model
from spotifyify.utils import coalesce_items


class Resource:
    def __init__(self, http: SpotifyAPIClient) -> None:
        self._http = http

    def _require_extended(self, operation: str) -> None:
        if self._http.api_mode != ApiMode.EXTENDED:
            raise SpotifyUnsupportedOperation(
                f"{operation} is unavailable in Development Mode. Use api_mode='extended' only for an app with Extended Quota access."
            )

    async def _search(
        self,
        kind: str,
        query: str,
        *,
        limit: int,
        offset: int,
        market: str | None = None,
    ) -> dict[str, Any]:
        maximum = 10 if self._http.api_mode == ApiMode.DEVELOPMENT else 50
        if not query.strip():
            raise ValueError("Search query must not be empty")
        if not 1 <= limit <= maximum or not 0 <= offset <= 1000:
            raise ValueError(f"Search requires limit 1..{maximum} and offset 0..1000")
        params: dict[str, Any] = {
            "q": query,
            "type": kind,
            "limit": limit,
            "offset": offset,
        }
        if market:
            params["market"] = market
        data = object_response(
            await self._http.get("/search", params=params, require_user=False)
        )
        return object_response(data.get(f"{kind}s"))

    async def _get_many[T: BaseModel](
        self,
        resource: str,
        ids: Iterable[str],
        model: type[T],
        batch_size: int,
        *,
        market: str | None = None,
    ) -> list[T | None]:
        values = coalesce_items(ids)
        params = {"market": market} if market else {}
        if self._http.api_mode == ApiMode.DEVELOPMENT:

            async def get_one(item_id: str) -> T | None:
                try:
                    data = await self._http.get(
                        f"/{resource}/{item_id}",
                        params=params or None,
                        require_user=False,
                    )
                except SpotifyAPIError as exc:
                    if exc.status_code == 404:
                        return None
                    raise
                return validate_model(model, data)

            return await bounded_map(
                get_one, values, concurrency=self._http.concurrency
            )

        async def get_batch(batch: list[str]) -> list[T | None]:
            data = await self._http.get(
                f"/{resource}",
                params={"ids": ",".join(batch), **params},
                require_user=False,
            )
            items = list_response(data, resource)
            if len(items) != len(batch):
                raise SpotifyResponseError(
                    "Batch response length does not match the requested IDs"
                )
            return [
                validate_model(model, item) if item is not None else None
                for item in items
            ]

        batches = await bounded_map(
            get_batch, chunks(values, batch_size), concurrency=self._http.concurrency
        )
        return [item for batch in batches for item in batch]

    async def _library_write(
        self, kind: str, ids: Iterable[str], *, remove: bool = False
    ) -> None:
        values = coalesce_items(ids)
        action = self._http.delete if remove else self._http.put
        if self._http.api_mode == ApiMode.DEVELOPMENT:
            for batch in chunks(values, 40):
                await action(
                    "/me/library",
                    params={
                        "uris": ",".join(f"spotify:{kind}:{value}" for value in batch)
                    },
                )
        else:
            for batch in chunks(values, 50):
                await action(f"/me/{kind}s", params={"ids": ",".join(batch)})

    async def _library_check(self, kind: str, ids: Iterable[str]) -> list[bool]:
        values = coalesce_items(ids)
        result: list[bool] = []
        modern = self._http.api_mode == ApiMode.DEVELOPMENT
        for batch in chunks(values, 40 if modern else 50):
            path = "/me/library/contains" if modern else f"/me/{kind}s/contains"
            params = (
                {"uris": ",".join(f"spotify:{kind}:{value}" for value in batch)}
                if modern
                else {"ids": ",".join(batch)}
            )
            data = list_response(await self._http.get(path, params=params))
            if len(data) != len(batch) or any(
                type(value) is not bool for value in data
            ):
                raise SpotifyResponseError(
                    "Contains response must have one boolean per requested item"
                )
            result.extend(data)
        return result
