from collections.abc import AsyncIterator, Iterable
from typing import Any

from spotifyify.http.response import list_response, validate_model
from spotifyify.namespaces.base import Resource
from spotifyify.pagination import iter_offset_items
from spotifyify.schemas import (
    Artist,
    ArtistDiscographyAlbum,
    PagingArtist,
    PagingArtistDiscographyAlbum,
    Track,
)
from spotifyify.utils import deprecated
from spotifyify.validation import market as validate_market
from spotifyify.validation import page as validate_page
from spotifyify.validation import spotify_id as validate_id


class Artists(Resource):
    async def search(
        self, query: str, *, limit: int = 10, offset: int = 0
    ) -> PagingArtist:
        validate_page(limit, offset)
        return validate_model(
            PagingArtist,
            await self._search("artist", query, limit=limit, offset=offset),
        )

    find = search

    async def get(self, artist_id: str) -> Artist:
        artist_id = validate_id(artist_id)
        data = await self._http.get(f"/artists/{artist_id}", require_user=False)
        return validate_model(Artist, data)

    async def get_many(self, artist_ids: Iterable[str]) -> list[Artist | None]:
        """Fetch any number of IDs, preserving order and missing positions."""
        return await self._get_many("artists", artist_ids, Artist, 50)

    async def top_tracks(self, artist_id: str, *, market: str = "US") -> list[Track]:
        artist_id = validate_id(artist_id)
        market = validate_market(market) or "US"
        self._require_extended("Artist top tracks")
        data = await self._http.get(
            f"/artists/{artist_id}/top-tracks",
            params={"market": market},
            require_user=False,
        )
        return [validate_model(Track, item) for item in list_response(data, "tracks")]

    async def albums(
        self,
        artist_id: str,
        *,
        include_groups: str | None = None,
        market: str | None = None,
        limit: int = 20,
        offset: int = 0,
    ) -> PagingArtistDiscographyAlbum:
        validate_page(limit, offset)
        artist_id = validate_id(artist_id)
        market = validate_market(market)
        params: dict[str, Any] = {"limit": limit, "offset": offset}
        if include_groups:
            params["include_groups"] = include_groups
        if market:
            params["market"] = market
        data = await self._http.get(
            f"/artists/{artist_id}/albums", params=params, require_user=False
        )
        return validate_model(PagingArtistDiscographyAlbum, data)

    @deprecated(
        "Spotify retired the Related Artists endpoint for most apps in "
        "November 2024; this call will likely fail with a 404."
    )
    async def related(self, artist_id: str) -> list[Artist]:
        artist_id = validate_id(artist_id)
        self._require_extended("Related artists")
        data = await self._http.get(
            f"/artists/{artist_id}/related-artists", require_user=False
        )
        return [validate_model(Artist, item) for item in list_response(data, "artists")]

    async def iter_search(
        self, query: str, *, limit: int = 10, offset: int = 0, **kwargs: Any
    ) -> AsyncIterator[Artist]:
        """Yield results across pages, stopping without prefetch when the caller stops."""
        async for item in iter_offset_items(
            self.search, limit=limit, offset=offset, query=query, **kwargs
        ):
            yield item

    async def iter_albums(
        self, artist_id: str, *, limit: int = 50, offset: int = 0, **kwargs: Any
    ) -> AsyncIterator[ArtistDiscographyAlbum]:
        """Yield results across pages, stopping without prefetch when the caller stops."""
        async for item in iter_offset_items(
            self.albums, limit=limit, offset=offset, artist_id=artist_id, **kwargs
        ):
            yield item
