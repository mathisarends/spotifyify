from typing import Any

from collections.abc import Iterable

from spotifyify.client import SpotifyClient
from spotifyify.schemas import (
    PagingArtistObject,
    PagingSavedAlbumObject,
    PagingSavedEpisodeObject,
    PagingSavedShowObject,
    PagingSavedTrackObject,
    PagingTrackObject,
)
from spotifyify.utils import coalesce_csv


class Library:
    def __init__(self, http: SpotifyClient) -> None:
        self._http = http

    async def saved_tracks(
        self,
        *,
        limit: int = 20,
        offset: int = 0,
        market: str | None = None,
    ) -> PagingSavedTrackObject:
        params: dict[str, Any] = {"limit": limit, "offset": offset}
        if market:
            params["market"] = market
        data = await self._http.get("/me/tracks", params=params) or {}
        return PagingSavedTrackObject.model_validate(data)

    async def saved_albums(
        self,
        *,
        limit: int = 20,
        offset: int = 0,
        market: str | None = None,
    ) -> PagingSavedAlbumObject:
        params: dict[str, Any] = {"limit": limit, "offset": offset}
        if market:
            params["market"] = market
        data = await self._http.get("/me/albums", params=params) or {}
        return PagingSavedAlbumObject.model_validate(data)

    async def saved_shows(
        self,
        *,
        limit: int = 20,
        offset: int = 0,
    ) -> PagingSavedShowObject:
        params: dict[str, Any] = {"limit": limit, "offset": offset}
        data = await self._http.get("/me/shows", params=params) or {}
        return PagingSavedShowObject.model_validate(data)

    async def saved_episodes(
        self,
        *,
        limit: int = 20,
        offset: int = 0,
    ) -> PagingSavedEpisodeObject:
        params: dict[str, Any] = {"limit": limit, "offset": offset}
        data = await self._http.get("/me/episodes", params=params) or {}
        return PagingSavedEpisodeObject.model_validate(data)

    async def save_tracks(self, track_ids: Iterable[str]) -> None:
        await self._http.put("/me/tracks", params={"ids": coalesce_csv(track_ids)})

    async def remove_tracks(self, track_ids: Iterable[str]) -> None:
        await self._http.delete("/me/tracks", params={"ids": coalesce_csv(track_ids)})

    async def save_albums(self, album_ids: Iterable[str]) -> None:
        await self._http.put("/me/albums", params={"ids": coalesce_csv(album_ids)})

    async def remove_albums(self, album_ids: Iterable[str]) -> None:
        await self._http.delete("/me/albums", params={"ids": coalesce_csv(album_ids)})

    async def save_shows(self, show_ids: Iterable[str]) -> None:
        await self._http.put("/me/shows", params={"ids": coalesce_csv(show_ids)})

    async def remove_shows(self, show_ids: Iterable[str]) -> None:
        await self._http.delete("/me/shows", params={"ids": coalesce_csv(show_ids)})

    async def save_episodes(self, episode_ids: Iterable[str]) -> None:
        await self._http.put("/me/episodes", params={"ids": coalesce_csv(episode_ids)})

    async def remove_episodes(self, episode_ids: Iterable[str]) -> None:
        await self._http.delete(
            "/me/episodes", params={"ids": coalesce_csv(episode_ids)}
        )

    async def check_tracks(self, track_ids: Iterable[str]) -> list[bool]:
        data = await self._http.get(
            "/me/tracks/contains", params={"ids": coalesce_csv(track_ids)}
        )
        return data if isinstance(data, list) else []

    async def check_albums(self, album_ids: Iterable[str]) -> list[bool]:
        data = await self._http.get(
            "/me/albums/contains", params={"ids": coalesce_csv(album_ids)}
        )
        return data if isinstance(data, list) else []

    async def check_shows(self, show_ids: Iterable[str]) -> list[bool]:
        data = await self._http.get(
            "/me/shows/contains", params={"ids": coalesce_csv(show_ids)}
        )
        return data if isinstance(data, list) else []

    async def check_episodes(self, episode_ids: Iterable[str]) -> list[bool]:
        data = await self._http.get(
            "/me/episodes/contains", params={"ids": coalesce_csv(episode_ids)}
        )
        return data if isinstance(data, list) else []

    async def top_tracks(
        self,
        *,
        time_range: str = "medium_term",
        limit: int = 20,
        offset: int = 0,
    ) -> PagingTrackObject:
        data = (
            await self._http.get(
                "/me/top/tracks",
                params={"time_range": time_range, "limit": limit, "offset": offset},
            )
            or {}
        )
        return PagingTrackObject.model_validate(data)

    async def top_artists(
        self,
        *,
        time_range: str = "medium_term",
        limit: int = 20,
        offset: int = 0,
    ) -> PagingArtistObject:
        data = (
            await self._http.get(
                "/me/top/artists",
                params={"time_range": time_range, "limit": limit, "offset": offset},
            )
            or {}
        )
        return PagingArtistObject.model_validate(data)
