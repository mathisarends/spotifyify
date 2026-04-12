from __future__ import annotations

from typing import TYPE_CHECKING, Any

from collections.abc import Iterable

from spotifyify.http.client import SpotifyAPIHttpClient
from spotifyify.schemas import Paging, Playlist
from spotifyify.utils import coalesce_items

if TYPE_CHECKING:
    from spotifyify.spotifyify import Spotifyify


class PlaylistsNamespace:
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
        params = {
            "q": query,
            "type": "playlist",
            "limit": limit,
            "offset": offset,
        }
        data = await self.http.get("/search", params=params, require_user=False) or {}
        playlists = data.get("playlists", {}) if isinstance(data, dict) else {}
        return Paging.model_validate(playlists)

    async def get(self, playlist_id: str, *, market: str | None = None) -> Playlist:
        params = {"market": market} if market else None
        data = (
            await self.http.get(
                f"/playlists/{playlist_id}",
                params=params,
                require_user=False,
            )
            or {}
        )
        return Playlist.model_validate(data)

    async def create(
        self,
        name: str,
        *,
        public: bool = False,
        collaborative: bool = False,
        description: str = "",
        user_id: str | None = None,
    ) -> Playlist:
        target_user = user_id
        if not target_user:
            me = await self._client.users.get_current()
            target_user = str(me.get("id") or "")
        data = (
            await self.http.post(
                f"/users/{target_user}/playlists",
                payload={
                    "name": name,
                    "public": public,
                    "collaborative": collaborative,
                    "description": description,
                },
            )
            or {}
        )
        return Playlist.model_validate(data)

    async def add(
        self,
        playlist_id: str,
        uris: Iterable[str],
        *,
        position: int | None = None,
    ) -> str | None:
        payload: dict[str, Any] = {"uris": coalesce_items(uris)}
        if position is not None:
            payload["position"] = position
        data = (
            await self.http.post(f"/playlists/{playlist_id}/tracks", payload=payload)
            or {}
        )
        return data.get("snapshot_id") if isinstance(data, dict) else None

    async def remove(self, playlist_id: str, uris: Iterable[str]) -> str | None:
        payload = {"tracks": [{"uri": uri} for uri in coalesce_items(uris)]}
        data = (
            await self.http.delete(f"/playlists/{playlist_id}/tracks", payload=payload)
            or {}
        )
        return data.get("snapshot_id") if isinstance(data, dict) else None

    async def reorder(
        self,
        playlist_id: str,
        *,
        range_start: int,
        insert_before: int,
        range_length: int = 1,
        snapshot_id: str | None = None,
    ) -> str | None:
        payload: dict[str, Any] = {
            "range_start": range_start,
            "insert_before": insert_before,
            "range_length": range_length,
        }
        if snapshot_id:
            payload["snapshot_id"] = snapshot_id
        data = (
            await self.http.put(f"/playlists/{playlist_id}/tracks", payload=payload)
            or {}
        )
        return data.get("snapshot_id") if isinstance(data, dict) else None
