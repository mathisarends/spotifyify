from collections.abc import AsyncIterator, Iterable
from typing import Any

from spotifyify.http.response import validate_model
from spotifyify.namespaces.base import Resource
from spotifyify.pagination import iter_offset_items
from spotifyify.schemas import (
    PagingSimplifiedEpisode,
    PagingSimplifiedShow,
    Show,
    SimplifiedEpisode,
    SimplifiedShow,
)
from spotifyify.validation import market as validate_market
from spotifyify.validation import page as validate_page
from spotifyify.validation import spotify_id as validate_id


class Shows(Resource):
    async def search(
        self, query: str, *, limit: int = 10, offset: int = 0, market: str | None = None
    ) -> PagingSimplifiedShow:
        validate_page(limit, offset)
        market = validate_market(market)
        return validate_model(
            PagingSimplifiedShow,
            await self._search(
                "show", query, limit=limit, offset=offset, market=market
            ),
        )

    find = search

    async def get(self, show_id: str, *, market: str | None = None) -> Show:
        market = validate_market(market)
        show_id = validate_id(show_id)
        data = await self._http.get(
            f"/shows/{show_id}",
            params={"market": market} if market else None,
            require_user=False,
        )
        return validate_model(Show, data)

    async def get_many(
        self, show_ids: Iterable[str], *, market: str | None = None
    ) -> list[SimplifiedShow | None]:
        """Fetch any number of IDs, preserving order and missing positions."""
        market = validate_market(market)
        return await self._get_many(
            "shows", show_ids, SimplifiedShow, 50, market=market
        )

    async def episodes(
        self,
        show_id: str,
        *,
        market: str | None = None,
        limit: int = 20,
        offset: int = 0,
    ) -> PagingSimplifiedEpisode:
        validate_page(limit, offset)
        market = validate_market(market)
        show_id = validate_id(show_id)
        params: dict[str, Any] = {"limit": limit, "offset": offset}
        if market:
            params["market"] = market
        data = await self._http.get(
            f"/shows/{show_id}/episodes", params=params, require_user=False
        )
        return validate_model(PagingSimplifiedEpisode, data)

    async def iter_search(
        self, query: str, *, limit: int = 10, offset: int = 0, **kwargs: Any
    ) -> AsyncIterator[SimplifiedShow]:
        """Yield results across pages, stopping without prefetch when the caller stops."""
        async for item in iter_offset_items(
            self.search, limit=limit, offset=offset, query=query, **kwargs
        ):
            yield item

    async def iter_episodes(
        self, show_id: str, *, limit: int = 50, offset: int = 0, **kwargs: Any
    ) -> AsyncIterator[SimplifiedEpisode | None]:
        """Yield results across pages, stopping without prefetch when the caller stops."""
        async for item in iter_offset_items(
            self.episodes, limit=limit, offset=offset, show_id=show_id, **kwargs
        ):
            yield item
