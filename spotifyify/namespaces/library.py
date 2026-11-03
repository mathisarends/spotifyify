from collections.abc import AsyncIterator, Iterable
from typing import Any

from spotifyify.http.response import validate_model
from spotifyify.namespaces.base import Resource
from spotifyify.pagination import iter_offset_items
from spotifyify.schemas import (
    Artist,
    PagingArtist,
    PagingSavedAlbum,
    PagingSavedEpisode,
    PagingSavedShow,
    PagingSavedTrack,
    PagingTrack,
    SavedAlbum,
    SavedEpisode,
    SavedShow,
    SavedTrack,
    Track,
)
from spotifyify.validation import market as validate_market
from spotifyify.validation import page as validate_page


class Library(Resource):
    async def saved_tracks(
        self,
        *,
        limit: int = 20,
        offset: int = 0,
        market: str | None = None,
    ) -> PagingSavedTrack:
        validate_page(limit, offset)
        market = validate_market(market)
        params: dict[str, Any] = {"limit": limit, "offset": offset}
        if market:
            params["market"] = market
        data = await self._http.get("/me/tracks", params=params)
        return validate_model(PagingSavedTrack, data)

    async def saved_albums(
        self,
        *,
        limit: int = 20,
        offset: int = 0,
        market: str | None = None,
    ) -> PagingSavedAlbum:
        validate_page(limit, offset)
        market = validate_market(market)
        params: dict[str, Any] = {"limit": limit, "offset": offset}
        if market:
            params["market"] = market
        data = await self._http.get("/me/albums", params=params)
        return validate_model(PagingSavedAlbum, data)

    async def saved_shows(
        self,
        *,
        limit: int = 20,
        offset: int = 0,
    ) -> PagingSavedShow:
        validate_page(limit, offset)
        params: dict[str, Any] = {"limit": limit, "offset": offset}
        data = await self._http.get("/me/shows", params=params)
        return validate_model(PagingSavedShow, data)

    async def saved_episodes(
        self,
        *,
        limit: int = 20,
        offset: int = 0,
    ) -> PagingSavedEpisode:
        validate_page(limit, offset)
        params: dict[str, Any] = {"limit": limit, "offset": offset}
        data = await self._http.get("/me/episodes", params=params)
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
        validate_page(limit, offset)
        if time_range not in {"short_term", "medium_term", "long_term"}:
            raise ValueError("time_range must be short_term, medium_term, or long_term")
        data = await self._http.get(
            "/me/top/tracks",
            params={"time_range": time_range, "limit": limit, "offset": offset},
        )
        return validate_model(PagingTrack, data)

    async def top_artists(
        self,
        *,
        time_range: str = "medium_term",
        limit: int = 20,
        offset: int = 0,
    ) -> PagingArtist:
        validate_page(limit, offset)
        if time_range not in {"short_term", "medium_term", "long_term"}:
            raise ValueError("time_range must be short_term, medium_term, or long_term")
        data = await self._http.get(
            "/me/top/artists",
            params={"time_range": time_range, "limit": limit, "offset": offset},
        )
        return validate_model(PagingArtist, data)

    async def iter_saved_tracks(
        self, *, limit: int = 50, offset: int = 0, **kwargs: Any
    ) -> AsyncIterator[SavedTrack]:
        """Yield results across pages, stopping without prefetch when the caller stops."""
        async for item in iter_offset_items(
            self.saved_tracks, limit=limit, offset=offset, **kwargs
        ):
            yield item

    async def iter_saved_albums(
        self, *, limit: int = 50, offset: int = 0, **kwargs: Any
    ) -> AsyncIterator[SavedAlbum]:
        """Yield results across pages, stopping without prefetch when the caller stops."""
        async for item in iter_offset_items(
            self.saved_albums, limit=limit, offset=offset, **kwargs
        ):
            yield item

    async def iter_saved_shows(
        self, *, limit: int = 50, offset: int = 0, **kwargs: Any
    ) -> AsyncIterator[SavedShow]:
        """Yield results across pages, stopping without prefetch when the caller stops."""
        async for item in iter_offset_items(
            self.saved_shows, limit=limit, offset=offset, **kwargs
        ):
            yield item

    async def iter_saved_episodes(
        self, *, limit: int = 50, offset: int = 0, **kwargs: Any
    ) -> AsyncIterator[SavedEpisode]:
        """Yield results across pages, stopping without prefetch when the caller stops."""
        async for item in iter_offset_items(
            self.saved_episodes, limit=limit, offset=offset, **kwargs
        ):
            yield item

    async def iter_top_tracks(
        self, *, limit: int = 50, offset: int = 0, **kwargs: Any
    ) -> AsyncIterator[Track]:
        """Yield results across pages, stopping without prefetch when the caller stops."""
        async for item in iter_offset_items(
            self.top_tracks, limit=limit, offset=offset, **kwargs
        ):
            yield item

    async def iter_top_artists(
        self, *, limit: int = 50, offset: int = 0, **kwargs: Any
    ) -> AsyncIterator[Artist]:
        """Yield results across pages, stopping without prefetch when the caller stops."""
        async for item in iter_offset_items(
            self.top_artists, limit=limit, offset=offset, **kwargs
        ):
            yield item
