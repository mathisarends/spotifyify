from collections.abc import AsyncIterator
from typing import Any
from spotifyify.pagination import iter_offset_items
from spotifyify.schemas import SimplifiedAlbum, SimplifiedTrack
from spotifyify.validation import spotify_id as validate_id
from spotifyify.validation import market as validate_market
from spotifyify.validation import page as validate_page
from spotifyify.namespaces.base import Resource
from spotifyify.http.response import validate_model

from collections.abc import Iterable

from spotifyify.schemas import (
    Album,
    PagingSimplifiedAlbum,
    PagingSimplifiedTrack,
)


class Albums(Resource):
    async def search(
        self, query: str, *, limit: int = 10, offset: int = 0, market: str | None = None
    ) -> PagingSimplifiedAlbum:
        validate_page(limit, offset)
        market = validate_market(market)
        return validate_model(
            PagingSimplifiedAlbum,
            await self._search(
                "album", query, limit=limit, offset=offset, market=market
            ),
        )

    find = search

    async def get(self, album_id: str, *, market: str | None = None) -> Album:
        album_id = validate_id(album_id)
        market = validate_market(market)
        data = (
            await self._http.get(
                f"/albums/{album_id}",
                params={"market": market} if market else None,
                require_user=False,
            )
            or {}
        )
        return validate_model(Album, data)

    async def get_many(
        self, album_ids: Iterable[str], *, market: str | None = None
    ) -> list[Album | None]:
        """Fetch any number of IDs, preserving order and missing positions."""
        market = validate_market(market)
        return await self._get_many("albums", album_ids, Album, 20, market=market)

    async def tracks(
        self,
        album_id: str,
        *,
        limit: int = 50,
        offset: int = 0,
        market: str | None = None,
    ) -> PagingSimplifiedTrack:
        validate_page(limit, offset)
        album_id = validate_id(album_id)
        market = validate_market(market)
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
        return validate_model(PagingSimplifiedTrack, data)

    async def new_releases(
        self,
        *,
        country: str | None = None,
        limit: int = 20,
        offset: int = 0,
    ) -> PagingSimplifiedAlbum:
        validate_page(limit, offset)
        country = validate_market(country)
        self._require_extended("New releases")
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
        return validate_model(PagingSimplifiedAlbum, albums)

    async def iter_search(
        self, query: str, *, limit: int = 10, offset: int = 0, **kwargs: Any
    ) -> AsyncIterator[SimplifiedAlbum]:
        """Yield results across pages, stopping without prefetch when the caller stops."""
        async for item in iter_offset_items(
            self.search, limit=limit, offset=offset, query=query, **kwargs
        ):
            yield item

    async def iter_tracks(
        self, album_id: str, *, limit: int = 50, offset: int = 0, **kwargs: Any
    ) -> AsyncIterator[SimplifiedTrack]:
        """Yield results across pages, stopping without prefetch when the caller stops."""
        async for item in iter_offset_items(
            self.tracks, limit=limit, offset=offset, album_id=album_id, **kwargs
        ):
            yield item
