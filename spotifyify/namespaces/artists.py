from typing import Any

from collections.abc import Iterable

from spotifyify.client import SpotifyClient
from spotifyify.schemas import (
    Artist,
    PagingArtistDiscographyAlbum,
    PagingArtist,
    Track,
)
from spotifyify.utils import coalesce_csv, deprecated


class Artists:
    def __init__(self, http: SpotifyClient) -> None:
        self._http = http

    async def find(
        self,
        query: str,
        *,
        limit: int = 10,
        offset: int = 0,
    ) -> PagingArtist:
        params: dict[str, Any] = {
            "q": query,
            "type": "artist",
            "limit": limit,
            "offset": offset,
        }
        data = await self._http.get("/search", params=params, require_user=False) or {}
        artists = data.get("artists", {}) if isinstance(data, dict) else {}
        return PagingArtist.model_validate(artists)

    async def get(self, artist_id: str) -> Artist:
        data = await self._http.get(f"/artists/{artist_id}", require_user=False) or {}
        return Artist.model_validate(data)

    async def get_many(self, artist_ids: Iterable[str]) -> list[Artist]:
        params: dict[str, Any] = {"ids": coalesce_csv(artist_ids)}
        data = await self._http.get("/artists", params=params, require_user=False)
        artists = data.get("artists", []) if isinstance(data, dict) else []
        return [Artist.model_validate(item) for item in artists if item]

    async def top_tracks(self, artist_id: str, *, market: str = "US") -> list[Track]:
        data = (
            await self._http.get(
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
    ) -> PagingArtistDiscographyAlbum:
        params: dict[str, Any] = {"limit": limit, "offset": offset}
        if include_groups:
            params["include_groups"] = include_groups
        if market:
            params["market"] = market
        data = (
            await self._http.get(
                f"/artists/{artist_id}/albums",
                params=params,
                require_user=False,
            )
            or {}
        )
        return PagingArtistDiscographyAlbum.model_validate(data)

    @deprecated(
        "Spotify retired the Related Artists endpoint for most apps in "
        "November 2024; this call will likely fail with a 404."
    )
    async def related(self, artist_id: str) -> list[Artist]:
        data = (
            await self._http.get(
                f"/artists/{artist_id}/related-artists",
                require_user=False,
            )
            or {}
        )
        artists = data.get("artists", []) if isinstance(data, dict) else []
        return [Artist.model_validate(item) for item in artists if item]
