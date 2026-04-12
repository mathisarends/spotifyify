from typing import Any

from collections.abc import Iterable

from spotifyify.client import SpotifyClient
from spotifyify.schemas import Episode, PagingSimplifiedEpisodeObject
from spotifyify.utils import coalesce_csv


class Episodes:
    def __init__(self, http: SpotifyClient) -> None:
        self._http = http

    async def find(
        self,
        query: str,
        *,
        limit: int = 10,
        offset: int = 0,
        market: str | None = None,
    ) -> PagingSimplifiedEpisodeObject:
        params: dict[str, Any] = {
            "q": query,
            "type": "episode",
            "limit": limit,
            "offset": offset,
        }
        if market:
            params["market"] = market
        data = await self._http.get("/search", params=params, require_user=False) or {}
        episodes = data.get("episodes", {}) if isinstance(data, dict) else {}
        return PagingSimplifiedEpisodeObject.model_validate(episodes)

    async def get(self, episode_id: str, *, market: str | None = None) -> Episode:
        data = (
            await self._http.get(
                f"/episodes/{episode_id}",
                params={"market": market} if market else None,
                require_user=False,
            )
            or {}
        )
        return Episode.model_validate(data)

    async def get_many(
        self,
        episode_ids: Iterable[str],
        *,
        market: str | None = None,
    ) -> list[Episode]:
        params: dict[str, Any] = {"ids": coalesce_csv(episode_ids)}
        if market:
            params["market"] = market
        data = await self._http.get("/episodes", params=params, require_user=False)
        episodes = data.get("episodes", []) if isinstance(data, dict) else []
        return [Episode.model_validate(item) for item in episodes if item]
