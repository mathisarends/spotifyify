from spotifyify.namespaces.base import Resource
from spotifyify.http.response import validate_model
from typing import Any

from collections.abc import Iterable

from spotifyify.schemas import (
    PagingArtist,
    PagingSavedAlbum,
    PagingSavedEpisode,
    PagingSavedShow,
    PagingSavedTrack,
    PagingTrack,
)


class Library(Resource):
    async def saved_tracks(
        self,
        *,
        limit: int = 20,
        offset: int = 0,
        market: str | None = None,
    ) -> PagingSavedTrack:
        params: dict[str, Any] = {"limit": limit, "offset": offset}
        if market:
            params["market"] = market
        data = await self._http.get("/me/tracks", params=params) or {}
        return validate_model(PagingSavedTrack, data)

    async def saved_albums(
        self,
        *,
        limit: int = 20,
        offset: int = 0,
        market: str | None = None,
    ) -> PagingSavedAlbum:
        params: dict[str, Any] = {"limit": limit, "offset": offset}
        if market:
            params["market"] = market
        data = await self._http.get("/me/albums", params=params) or {}
        return validate_model(PagingSavedAlbum, data)

    async def saved_shows(
        self,
        *,
        limit: int = 20,
        offset: int = 0,
    ) -> PagingSavedShow:
        params: dict[str, Any] = {"limit": limit, "offset": offset}
        data = await self._http.get("/me/shows", params=params) or {}
        return validate_model(PagingSavedShow, data)

    async def saved_episodes(
        self,
        *,
        limit: int = 20,
        offset: int = 0,
    ) -> PagingSavedEpisode:
        params: dict[str, Any] = {"limit": limit, "offset": offset}
        data = await self._http.get("/me/episodes", params=params) or {}
        return validate_model(PagingSavedEpisode, data)

    async def save_tracks(self, track_ids: Iterable[str]) -> None:
        await self._library_write("track", track_ids, remove=False)

    async def remove_tracks(self, track_ids: Iterable[str]) -> None:
        await self._library_write("track", track_ids, remove=True)

    async def save_albums(self, album_ids: Iterable[str]) -> None:
        await self._library_write("album", album_ids, remove=False)

    async def remove_albums(self, album_ids: Iterable[str]) -> None:
        await self._library_write("album", album_ids, remove=True)

    async def save_shows(self, show_ids: Iterable[str]) -> None:
        await self._library_write("show", show_ids, remove=False)

    async def remove_shows(self, show_ids: Iterable[str]) -> None:
        await self._library_write("show", show_ids, remove=True)

    async def save_episodes(self, episode_ids: Iterable[str]) -> None:
        await self._library_write("episode", episode_ids, remove=False)

    async def remove_episodes(self, episode_ids: Iterable[str]) -> None:
        await self._library_write("episode", episode_ids, remove=True)

    async def check_tracks(self, track_ids: Iterable[str]) -> list[bool]:
        return await self._library_check("track", track_ids)

    async def check_albums(self, album_ids: Iterable[str]) -> list[bool]:
        return await self._library_check("album", album_ids)

    async def check_shows(self, show_ids: Iterable[str]) -> list[bool]:
        return await self._library_check("show", show_ids)

    async def check_episodes(self, episode_ids: Iterable[str]) -> list[bool]:
        return await self._library_check("episode", episode_ids)

    async def top_tracks(
        self,
        *,
        time_range: str = "medium_term",
        limit: int = 20,
        offset: int = 0,
    ) -> PagingTrack:
        data = (
            await self._http.get(
                "/me/top/tracks",
                params={"time_range": time_range, "limit": limit, "offset": offset},
            )
            or {}
        )
        return validate_model(PagingTrack, data)

    async def top_artists(
        self,
        *,
        time_range: str = "medium_term",
        limit: int = 20,
        offset: int = 0,
    ) -> PagingArtist:
        data = (
            await self._http.get(
                "/me/top/artists",
                params={"time_range": time_range, "limit": limit, "offset": offset},
            )
            or {}
        )
        return validate_model(PagingArtist, data)
