from __future__ import annotations

from typing import TYPE_CHECKING

from collections.abc import Iterable

from spotifyify.http.client import SpotifyAPIHttpClient
from spotifyify.schemas import Paging
from spotifyify.utils import coalesce_csv

if TYPE_CHECKING:
    from spotifyify.spotifyify import Spotifyify


class LibraryNamespace:
    def __init__(self, client: Spotifyify) -> None:
        self._client = client

    @property
    def http(self) -> SpotifyAPIHttpClient:
        return self._client.http

    async def saved_tracks(
        self,
        *,
        limit: int = 20,
        offset: int = 0,
        market: str | None = None,
    ) -> Paging:
        params: dict[str, int | str] = {"limit": limit, "offset": offset}
        if market:
            params["market"] = market
        data = await self.http.get("/me/tracks", params=params) or {}
        return Paging.model_validate(data)

    async def saved_albums(
        self,
        *,
        limit: int = 20,
        offset: int = 0,
        market: str | None = None,
    ) -> Paging:
        params: dict[str, int | str] = {"limit": limit, "offset": offset}
        if market:
            params["market"] = market
        data = await self.http.get("/me/albums", params=params) or {}
        return Paging.model_validate(data)

    async def save_tracks(self, track_ids: Iterable[str]) -> None:
        await self.http.put("/me/tracks", params={"ids": coalesce_csv(track_ids)})

    async def save_albums(self, album_ids: Iterable[str]) -> None:
        await self.http.put("/me/albums", params={"ids": coalesce_csv(album_ids)})

    async def top_tracks(
        self,
        *,
        time_range: str = "medium_term",
        limit: int = 20,
        offset: int = 0,
    ) -> Paging:
        data = (
            await self.http.get(
                "/me/top/tracks",
                params={"time_range": time_range, "limit": limit, "offset": offset},
            )
            or {}
        )
        return Paging.model_validate(data)

    async def top_artists(
        self,
        *,
        time_range: str = "medium_term",
        limit: int = 20,
        offset: int = 0,
    ) -> Paging:
        data = (
            await self.http.get(
                "/me/top/artists",
                params={"time_range": time_range, "limit": limit, "offset": offset},
            )
            or {}
        )
        return Paging.model_validate(data)

    async def recently_played(
        self,
        *,
        limit: int = 20,
        after: int | None = None,
        before: int | None = None,
    ) -> Paging:
        params: dict[str, int] = {"limit": limit}
        if after is not None:
            params["after"] = after
        if before is not None:
            params["before"] = before
        data = await self.http.get("/me/player/recently-played", params=params) or {}
        return Paging.model_validate(data)
