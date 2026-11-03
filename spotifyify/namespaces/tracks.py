from spotifyify.namespaces.base import Resource
from spotifyify.http.response import validate_model

from collections.abc import Iterable

from spotifyify.schemas import (
    PagingTrack,
    Track,
)


class Tracks(Resource):
    async def search(
        self, query: str, *, limit: int = 10, offset: int = 0, market: str | None = None
    ) -> PagingTrack:
        return validate_model(
            PagingTrack,
            await self._search(
                "track", query, limit=limit, offset=offset, market=market
            ),
        )

    find = search

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
    ) -> list[Track | None]:
        """Fetch any number of IDs, preserving order and missing positions."""
        return await self._get_many("tracks", track_ids, Track, 50, market=market)
