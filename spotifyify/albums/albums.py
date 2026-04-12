from __future__ import annotations

from typing import TYPE_CHECKING, Any

from collections.abc import Iterable

from spotifyify.http.client import SpotifyAPIHttpClient
from spotifyify.schemas import Album, Paging
from spotifyify.utils import coalesce_csv

if TYPE_CHECKING:
    from spotifyify.spotifyify import Spotifyify


class AlbumsNamespace:
    def __init__(self, client: Spotifyify) -> None:
        self._client = client

    @property
    def http(self) -> SpotifyAPIHttpClient:
        return self._client.http

    async def get(self, album_id: str, *, market: str | None = None) -> Album:
        data = (
            await self.http.get(
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
        data = await self.http.get("/albums", params=params, require_user=False)
        albums = data.get("albums", []) if isinstance(data, dict) else []
        return [Album.model_validate(item) for item in albums if item]

    async def tracks(
        self,
        album_id: str,
        *,
        limit: int = 50,
        offset: int = 0,
        market: str | None = None,
    ) -> Paging:
        params: dict[str, Any] = {"limit": limit, "offset": offset}
        if market:
            params["market"] = market
        data = (
            await self.http.get(
                f"/albums/{album_id}/tracks",
                params=params,
                require_user=False,
            )
            or {}
        )
        return Paging.model_validate(data)

    async def new_releases(
        self,
        *,
        country: str | None = None,
        limit: int = 20,
        offset: int = 0,
    ) -> Paging:
        params: dict[str, Any] = {"limit": limit, "offset": offset}
        if country:
            params["country"] = country
        data = (
            await self.http.get(
                "/browse/new-releases",
                params=params,
                require_user=False,
            )
            or {}
        )
        albums = data.get("albums", {}) if isinstance(data, dict) else {}
        return Paging.model_validate(albums)
