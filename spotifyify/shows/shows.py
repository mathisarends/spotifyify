from __future__ import annotations

from typing import TYPE_CHECKING, Any

from spotifyify.http.client import SpotifyAPIHttpClient
from spotifyify.schemas import Paging, Show

if TYPE_CHECKING:
    from spotifyify.spotifyify import Spotifyify


class ShowsNamespace:
    def __init__(self, client: Spotifyify) -> None:
        self._client = client

    @property
    def http(self) -> SpotifyAPIHttpClient:
        return self._client.http

    async def find(
        self,
        query: str,
        *,
        limit: int = 10,
        offset: int = 0,
        market: str | None = None,
    ) -> Paging:
        params: dict[str, Any] = {
            "q": query,
            "type": "show",
            "limit": limit,
            "offset": offset,
        }
        if market:
            params["market"] = market
        data = await self.http.get("/search", params=params, require_user=False) or {}
        shows = data.get("shows", {}) if isinstance(data, dict) else {}
        return Paging.model_validate(shows)

    async def get(self, show_id: str, *, market: str | None = None) -> Show:
        data = (
            await self.http.get(
                f"/shows/{show_id}",
                params={"market": market} if market else None,
                require_user=False,
            )
            or {}
        )
        return Show.model_validate(data)

    async def episodes(
        self,
        show_id: str,
        *,
        market: str | None = None,
        limit: int = 20,
        offset: int = 0,
    ) -> Paging:
        params: dict[str, Any] = {"limit": limit, "offset": offset}
        if market:
            params["market"] = market
        data = (
            await self.http.get(
                f"/shows/{show_id}/episodes",
                params=params,
                require_user=False,
            )
            or {}
        )
        return Paging.model_validate(data)
