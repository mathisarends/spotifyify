from typing import Any

from collections.abc import Iterable

from spotifyify.client import SpotifyClient
from spotifyify.schemas import (
    PagingSimplifiedEpisodeObject,
    PagingSimplifiedShowObject,
    Show,
    SimplifiedShow,
)
from spotifyify.utils import coalesce_csv


class Shows:
    def __init__(self, http: SpotifyClient) -> None:
        self._http = http

    async def find(
        self,
        query: str,
        *,
        limit: int = 10,
        offset: int = 0,
        market: str | None = None,
    ) -> PagingSimplifiedShowObject:
        params: dict[str, Any] = {
            "q": query,
            "type": "show",
            "limit": limit,
            "offset": offset,
        }
        if market:
            params["market"] = market
        data = await self._http.get("/search", params=params, require_user=False) or {}
        shows = data.get("shows", {}) if isinstance(data, dict) else {}
        return PagingSimplifiedShowObject.model_validate(shows)

    async def get(self, show_id: str, *, market: str | None = None) -> Show:
        data = (
            await self._http.get(
                f"/shows/{show_id}",
                params={"market": market} if market else None,
                require_user=False,
            )
            or {}
        )
        return Show.model_validate(data)

    async def get_many(
        self, show_ids: Iterable[str], *, market: str | None = None
    ) -> list[SimplifiedShow]:
        params: dict[str, Any] = {"ids": coalesce_csv(show_ids)}
        if market:
            params["market"] = market
        data = await self._http.get("/shows", params=params, require_user=False)
        shows = data.get("shows", []) if isinstance(data, dict) else []
        return [SimplifiedShow.model_validate(item) for item in shows if item]

    async def episodes(
        self,
        show_id: str,
        *,
        market: str | None = None,
        limit: int = 20,
        offset: int = 0,
    ) -> PagingSimplifiedEpisodeObject:
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
        return PagingSimplifiedEpisodeObject.model_validate(data)
