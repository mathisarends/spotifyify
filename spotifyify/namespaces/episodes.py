from collections.abc import AsyncIterator
from typing import Any
from spotifyify.pagination import iter_offset_items
from spotifyify.schemas import SimplifiedEpisode
from spotifyify.validation import spotify_id as validate_id
from spotifyify.validation import market as validate_market
from spotifyify.validation import page as validate_page
from spotifyify.namespaces.base import Resource
from spotifyify.http.response import validate_model

from collections.abc import Iterable

from spotifyify.schemas import Episode, PagingSimplifiedEpisode


class Episodes(Resource):
    async def search(
        self, query: str, *, limit: int = 10, offset: int = 0, market: str | None = None
    ) -> PagingSimplifiedEpisode:
        validate_page(limit, offset)
        market = validate_market(market)
        return validate_model(
            PagingSimplifiedEpisode,
            await self._search(
                "episode", query, limit=limit, offset=offset, market=market
            ),
        )

    find = search

    async def get(self, episode_id: str, *, market: str | None = None) -> Episode:
        episode_id = validate_id(episode_id)
        market = validate_market(market)
        data = (
            await self._http.get(
                f"/episodes/{episode_id}",
                params={"market": market} if market else None,
                require_user=False,
            )
            or {}
        )
        return validate_model(Episode, data)

    async def get_many(
        self, episode_ids: Iterable[str], *, market: str | None = None
    ) -> list[Episode | None]:
        """Fetch any number of IDs, preserving order and missing positions."""
        market = validate_market(market)
        return await self._get_many("episodes", episode_ids, Episode, 50, market=market)

    async def iter_search(
        self, query: str, *, limit: int = 10, offset: int = 0, **kwargs: Any
    ) -> AsyncIterator[SimplifiedEpisode | None]:
        """Yield results across pages, stopping without prefetch when the caller stops."""
        async for item in iter_offset_items(
            self.search, limit=limit, offset=offset, query=query, **kwargs
        ):
            yield item
