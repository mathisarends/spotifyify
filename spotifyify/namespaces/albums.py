from typing import Any

from collections.abc import Iterable

from spotifyify.client import SpotifyClient
from spotifyify.schemas import (
    Album,
    PagingSimplifiedAlbum,
    PagingSimplifiedTrack,
)
from spotifyify.utils import coalesce_csv


class Albums:
    def __init__(self, http: SpotifyClient) -> None:
        self._http = http

    async def find(
        self,
        query: str,
        *,
        limit: int = 10,
        offset: int = 0,
        market: str | None = None,
    ) -> PagingSimplifiedAlbum:
        params: dict[str, Any] = {
            "q": query,
            "type": "album",
            "limit": limit,
            "offset": offset,
        }
        if market:
            params["market"] = market
        data = await self._http.get("/search", params=params, require_user=False) or {}
        albums = data.get("albums", {}) if isinstance(data, dict) else {}
        return PagingSimplifiedAlbum.model_validate(albums)

    async def get(self, album_id: str, *, market: str | None = None) -> Album:
        data = (
            await self._http.get(
                f"/albums/{album_id}",
                params={"market": market} if market else None,
                require_user=False,
            )
            or {}
        )
        return Album.model_validate(data)

    async def get_many(
        self, album_ids: Iterable[str], *, market: str | None = None
    ) -> list[Album]:
        params: dict[str, Any] = {"ids": coalesce_csv(album_ids)}
        if market:
            params["market"] = market
        data = await self._http.get("/albums", params=params, require_user=False)
        albums = data.get("albums", []) if isinstance(data, dict) else []
        return [Album.model_validate(item) for item in albums if item]

    async def tracks(
        self,
        album_id: str,
        *,
        limit: int = 50,
        offset: int = 0,
        market: str | None = None,
    ) -> PagingSimplifiedTrack:
        params: dict[str, Any] = {"limit": limit, "offset": offset}
        if market:
            params["market"] = market
        data = (
            await self._http.get(
                f"/albums/{album_id}/tracks",
                params=params,
                require_user=False,
            )
            or {}
        )
        return PagingSimplifiedTrack.model_validate(data)

    async def new_releases(
        self,
        *,
        country: str | None = None,
        limit: int = 20,
        offset: int = 0,
    ) -> PagingSimplifiedAlbum:
        params: dict[str, Any] = {"limit": limit, "offset": offset}
        if country:
            params["country"] = country
        data = (
            await self._http.get(
                "/browse/new-releases",
                params=params,
                require_user=False,
            )
            or {}
        )
        albums = data.get("albums", {}) if isinstance(data, dict) else {}
        return PagingSimplifiedAlbum.model_validate(albums)
