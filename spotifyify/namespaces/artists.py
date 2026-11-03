from spotifyify.namespaces.base import Resource
from spotifyify.http.response import validate_model
from typing import Any

from collections.abc import Iterable

from spotifyify.schemas import (
    Artist,
    PagingArtistDiscographyAlbum,
    PagingArtist,
    Track,
)
from spotifyify.utils import deprecated


class Artists(Resource):
    async def search(
        self, query: str, *, limit: int = 10, offset: int = 0
    ) -> PagingArtist:
        return validate_model(
            PagingArtist,
            await self._search("artist", query, limit=limit, offset=offset),
        )

    find = search

    async def get(self, artist_id: str) -> Artist:
        data = await self._http.get(f"/artists/{artist_id}", require_user=False) or {}
        return validate_model(Artist, data)

    async def get_many(self, artist_ids: Iterable[str]) -> list[Artist | None]:
        """Fetch any number of IDs, preserving order and missing positions."""
        return await self._get_many("artists", artist_ids, Artist, 50)

    async def top_tracks(self, artist_id: str, *, market: str = "US") -> list[Track]:
        self._require_extended("Artist top tracks")
        data = (
            await self._http.get(
                f"/artists/{artist_id}/top-tracks",
                params={"market": market},
                require_user=False,
            )
            or {}
        )
        tracks = data.get("tracks", []) if isinstance(data, dict) else []
        return [validate_model(Track, item) for item in tracks if item]

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
        return validate_model(PagingArtistDiscographyAlbum, data)

    @deprecated(
        "Spotify retired the Related Artists endpoint for most apps in "
        "November 2024; this call will likely fail with a 404."
    )
    async def related(self, artist_id: str) -> list[Artist]:
        self._require_extended("Related artists")
        data = (
            await self._http.get(
                f"/artists/{artist_id}/related-artists",
                require_user=False,
            )
            or {}
        )
        artists = data.get("artists", []) if isinstance(data, dict) else []
        return [validate_model(Artist, item) for item in artists if item]
