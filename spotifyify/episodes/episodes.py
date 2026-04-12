from __future__ import annotations

from typing import TYPE_CHECKING

from collections.abc import Iterable

from spotifyify.http.client import SpotifyAPIHttpClient
from spotifyify.schemas import Episode
from spotifyify.utils import coalesce_csv

if TYPE_CHECKING:
    from spotifyify.spotifyify import Spotifyify


class EpisodesNamespace:
    def __init__(self, client: Spotifyify) -> None:
        self._client = client

    @property
    def http(self) -> SpotifyAPIHttpClient:
        return self._client.http

    async def get(self, episode_id: str, *, market: str | None = None) -> Episode:
        data = (
            await self.http.get(
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
        params: dict[str, str] = {"ids": coalesce_csv(episode_ids)}
        if market:
            params["market"] = market
        data = await self.http.get("/episodes", params=params, require_user=False)
        episodes = data.get("episodes", []) if isinstance(data, dict) else []
        return [Episode.model_validate(item) for item in episodes if item]
