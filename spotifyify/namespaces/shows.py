from spotifyify.namespaces.base import Resource
from spotifyify.http.response import validate_model
from typing import Any

from collections.abc import Iterable

from spotifyify.schemas import (
    PagingSimplifiedEpisode,
    PagingSimplifiedShow,
    Show,
    SimplifiedShow,
)


class Shows(Resource):
    async def search(
        self, query: str, *, limit: int = 10, offset: int = 0, market: str | None = None
    ) -> PagingSimplifiedShow:
        return validate_model(
            PagingSimplifiedShow,
            await self._search(
                "show", query, limit=limit, offset=offset, market=market
            ),
        )

    find = search

    async def get(self, show_id: str, *, market: str | None = None) -> Show:
        data = (
            await self._http.get(
                f"/shows/{show_id}",
                params={"market": market} if market else None,
                require_user=False,
            )
            or {}
        )
        return validate_model(Show, data)

    async def get_many(
        self, show_ids: Iterable[str], *, market: str | None = None
    ) -> list[SimplifiedShow | None]:
        """Fetch any number of IDs, preserving order and missing positions."""
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
        params: dict[str, Any] = {"limit": limit, "offset": offset}
        if market:
            params["market"] = market
        data = (
            await self._http.get(
                f"/shows/{show_id}/episodes",
                params=params,
                require_user=False,
            )
            or {}
        )
        return validate_model(PagingSimplifiedEpisode, data)
