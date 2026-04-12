from typing import Any

from collections.abc import Iterable

from spotifyify.client import SpotifyClient
from spotifyify.schemas import (
    AudioFeatures,
    AudioFeaturesObject,
    PagingTrackObject,
    Recommendations,
    Track,
)
from spotifyify.utils import coalesce_csv


class Tracks:
    def __init__(self, http: SpotifyClient) -> None:
        self._http = http

    async def find(
        self,
        query: str,
        *,
        limit: int = 10,
        offset: int = 0,
        market: str | None = None,
    ) -> PagingTrackObject:
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
        return PagingTrackObject.model_validate(tracks)

    async def get(self, track_id: str, *, market: str | None = None) -> Track:
        data = (
            await self._http.get(
                f"/tracks/{track_id}",
                params={"market": market} if market else None,
                require_user=False,
            )
            or {}
        )
        return Track.model_validate(data)

    async def get_many(
        self, track_ids: Iterable[str], *, market: str | None = None
    ) -> list[Track]:
        params: dict[str, Any] = {"ids": coalesce_csv(track_ids)}
        if market:
            params["market"] = market
        data = await self._http.get("/tracks", params=params, require_user=False)
        tracks = data.get("tracks", []) if isinstance(data, dict) else []
        return [Track.model_validate(item) for item in tracks if item]

    async def audio_features(self, track_ids: Iterable[str]) -> list[AudioFeatures]:
        data = await self._http.get(
            "/audio-features",
            params={"ids": coalesce_csv(track_ids)},
            require_user=False,
        )
        features = data.get("audio_features", []) if isinstance(data, dict) else []
        return [AudioFeaturesObject.model_validate(item) for item in features if item]

    async def recommendations(
        self,
        *,
        seed_artists: Iterable[str] = (),
        seed_tracks: Iterable[str] = (),
        seed_genres: Iterable[str] = (),
        limit: int = 20,
        market: str | None = None,
    ) -> Recommendations:
        params: dict[str, Any] = {"limit": limit}
        if seed_artists:
            params["seed_artists"] = coalesce_csv(seed_artists)
        if seed_tracks:
            params["seed_tracks"] = coalesce_csv(seed_tracks)
        if seed_genres:
            params["seed_genres"] = coalesce_csv(seed_genres)
        if market:
            params["market"] = market
        data = (
            await self._http.get(
                "/recommendations",
                params=params,
                require_user=False,
            )
            or {}
        )
        return Recommendations.model_validate(data)
