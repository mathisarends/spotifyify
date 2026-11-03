from collections.abc import AsyncIterator
from typing import Any
from spotifyify.pagination import iter_offset_items
from spotifyify.schemas import Track
from spotifyify.validation import spotify_id as validate_id
from spotifyify.validation import market as validate_market
from spotifyify.validation import page as validate_page
from spotifyify.namespaces.base import Resource
from spotifyify.http.response import validate_model

from collections.abc import Iterable

from spotifyify.schemas import (
    PagingTrack,
)


class Tracks(Resource):
    async def search(
        self, query: str, *, limit: int = 10, offset: int = 0, market: str | None = None
    ) -> PagingTrack:
        validate_page(limit, offset)
        market = validate_market(market)
        return validate_model(
            PagingTrack,
            await self._search(
                "track", query, limit=limit, offset=offset, market=market
            ),
        )

    find = search

    async def get(self, track_id: str, *, market: str | None = None) -> Track:
        market = validate_market(market)
        track_id = validate_id(track_id)
        data = (
            await self._http.get(
                f"/tracks/{track_id}",
                params={"market": market} if market else None,
                require_user=False,
            )
            or {}
        )
        return validate_model(Track, data)

    async def get_many(
        self, track_ids: Iterable[str], *, market: str | None = None
    ) -> list[Track | None]:
        """Fetch any number of IDs, preserving order and missing positions."""
        market = validate_market(market)
        return await self._get_many("tracks", track_ids, Track, 50, market=market)

    async def iter_search(
        self, query: str, *, limit: int = 10, offset: int = 0, **kwargs: Any
    ) -> AsyncIterator[Track]:
        """Yield results across pages, stopping without prefetch when the caller stops."""
        async for item in iter_offset_items(
            self.search, limit=limit, offset=offset, query=query, **kwargs
        ):
            yield item
