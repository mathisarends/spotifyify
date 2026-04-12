from __future__ import annotations

from typing import TYPE_CHECKING, Any

from spotifyify.http.client import SpotifyAPIHttpClient
from spotifyify.schemas import Artist, Paging, Track

if TYPE_CHECKING:
    from spotifyify.spotifyify import Spotifyify


class ArtistsNamespace:
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
    ) -> Paging:
        params: dict[str, Any] = {
            "q": query,
            "type": "artist",
            "limit": limit,
            "offset": offset,
        }
        data = await self.http.get("/search", params=params, require_user=False) or {}
        artists = data.get("artists", {}) if isinstance(data, dict) else {}
        return Paging.model_validate(artists)

    async def get(self, artist_id: str) -> Artist:
        data = await self.http.get(f"/artists/{artist_id}", require_user=False) or {}
        return Artist.model_validate(data)

    async def top_tracks(self, artist_id: str, *, market: str = "US") -> list[Track]:
        data = (
            await self.http.get(
                f"/artists/{artist_id}/top-tracks",
                params={"market": market},
                require_user=False,
            )
            or {}
        )
        tracks = data.get("tracks", []) if isinstance(data, dict) else []
        return [Track.model_validate(item) for item in tracks if item]

    async def albums(
        self,
        artist_id: str,
        *,
        include_groups: str | None = None,
        market: str | None = None,
        limit: int = 20,
        offset: int = 0,
    ) -> Paging:
        params: dict[str, Any] = {"limit": limit, "offset": offset}
        if include_groups:
            params["include_groups"] = include_groups
        if market:
            params["market"] = market
        data = (
            await self.http.get(
                f"/artists/{artist_id}/albums",
                params=params,
                require_user=False,
            )
            or {}
        )
        return Paging.model_validate(data)

    async def related(self, artist_id: str) -> list[Artist]:
        data = (
            await self.http.get(
                f"/artists/{artist_id}/related-artists",
                require_user=False,
            )
            or {}
        )
        artists = data.get("artists", []) if isinstance(data, dict) else []
        return [Artist.model_validate(item) for item in artists if item]
