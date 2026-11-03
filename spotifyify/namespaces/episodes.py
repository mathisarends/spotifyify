from spotifyify.namespaces.base import Resource
from spotifyify.http.response import validate_model

from collections.abc import Iterable

from spotifyify.schemas import Episode, PagingSimplifiedEpisode


class Episodes(Resource):
    async def search(
        self, query: str, *, limit: int = 10, offset: int = 0, market: str | None = None
    ) -> PagingSimplifiedEpisode:
        return validate_model(
            PagingSimplifiedEpisode,
            await self._search(
                "episode", query, limit=limit, offset=offset, market=market
            ),
        )

    find = search

    async def get(self, episode_id: str, *, market: str | None = None) -> Episode:
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
        return await self._get_many("episodes", episode_ids, Episode, 50, market=market)
