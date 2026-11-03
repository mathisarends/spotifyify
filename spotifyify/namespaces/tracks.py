from spotifyify.http.response import validate_model
from typing import Any

from collections.abc import Iterable

from spotifyify.client import SpotifyAPIClient
from spotifyify.schemas import (
    PagingTrack,
    Track,
)
from spotifyify.utils import coalesce_csv


class Tracks:
    def __init__(self, http: SpotifyAPIClient) -> None:
        self._http = http

    async def find(
        self,
        query: str,
        *,
        limit: int = 10,
        offset: int = 0,
        market: str | None = None,
    ) -> PagingTrack:
        params: dict[str, Any] = {
            "q": query,
            "type": "track",
            "limit": limit,
            "offset": offset,
        }
        if market:
            params["market"] = market
        data = await self._http.get("/search", params=params, require_user=False) or {}
        tracks = data.get("tracks", {}) if isinstance(data, dict) else {}
        return validate_model(PagingTrack, tracks)

    async def get(self, track_id: str, *, market: str | None = None) -> Track:
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
    ) -> list[Track]:
        params: dict[str, Any] = {"ids": coalesce_csv(track_ids)}
        if market:
            params["market"] = market
        data = await self._http.get("/tracks", params=params, require_user=False)
        tracks = data.get("tracks", []) if isinstance(data, dict) else []
        return [validate_model(Track, item) for item in tracks if item]
