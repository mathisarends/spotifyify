from __future__ import annotations

from spotifyify.namespaces.base import Resource
from spotifyify.config import ApiMode
from spotifyify.exceptions import SpotifyResponseError

from spotifyify.http.response import validate_model

from typing import TYPE_CHECKING, Any

from collections.abc import Iterable

from spotifyify.schemas import (
    Image,
    PagingPlaylist,
    PagingPlaylistTrack,
    Playlist,
    PlaylistProjection,
)
from spotifyify.utils import coalesce_csv, coalesce_items

if TYPE_CHECKING:
    from spotifyify.spotifyify import Spotifyify


_MAX_ITEMS_PER_REQUEST = 100


class Playlists(Resource):
    def __init__(self, client: Spotifyify) -> None:
        self._client = client
        super().__init__(client.http)

    async def search(
        self, query: str, *, limit: int = 10, offset: int = 0
    ) -> PagingPlaylist:
        return validate_model(
            PagingPlaylist,
            await self._search("playlist", query, limit=limit, offset=offset),
        )

    find = search

    async def get(self, playlist_id: str, *, market: str | None = None) -> Playlist:
        params = {"market": market} if market else None
        data = (
            await self._http.get(
                f"/playlists/{playlist_id}",
                params=params,
                require_user=False,
            )
            or {}
        )
        return validate_model(Playlist, data)

    async def list(
        self,
        *,
        user_id: str | None = None,
        limit: int = 50,
        offset: int = 0,
    ) -> PagingPlaylist:
        if user_id:
            self._require_extended("Other users playlists")
            path = f"/users/{user_id}/playlists"
        else:
            path = "/me/playlists"
        params: dict[str, Any] = {"limit": limit, "offset": offset}
        data = await self._http.get(path, params=params) or {}
        return validate_model(PagingPlaylist, data)

    async def items(
        self,
        playlist_id: str,
        *,
        market: str | None = None,
        fields: str | None = None,
        limit: int = 20,
        offset: int = 0,
        additional_types: Iterable[str] | None = None,
    ) -> PagingPlaylistTrack | PlaylistProjection:
        params: dict[str, Any] = {"limit": limit, "offset": offset}
        if market:
            params["market"] = market
        if fields:
            params["fields"] = fields
        if additional_types is not None:
            params["additional_types"] = coalesce_csv(additional_types)
        modern = self._http.api_mode == ApiMode.DEVELOPMENT
        data = await self._http.get(
            f"/playlists/{playlist_id}/{'items' if modern else 'tracks'}",
            params=params,
            require_user=modern,
        )
        return validate_model(
            PlaylistProjection if fields is not None else PagingPlaylistTrack, data
        )

    tracks = items

    async def create(
        self,
        name: str,
        *,
        public: bool = False,
        collaborative: bool = False,
        description: str = "",
        user_id: str | None = None,
    ) -> Playlist:
        if self._http.api_mode == ApiMode.DEVELOPMENT:
            if user_id is not None:
                self._require_extended("Creating a playlist for a supplied user_id")
            path = "/me/playlists"
        else:
            target_user = user_id
            if not target_user:
                me = await self._client.users.me()
                target_user = me.id
            if not target_user:
                raise SpotifyResponseError("Current user response is missing an ID")
            path = f"/users/{target_user}/playlists"
        data = (
            await self._http.post(
                path,
                payload={
                    "name": name,
                    "public": public,
                    "collaborative": collaborative,
                    "description": description,
                },
            )
            or {}
        )
        return validate_model(Playlist, data)

    async def update(
        self,
        playlist_id: str,
        *,
        name: str | None = None,
        public: bool | None = None,
        collaborative: bool | None = None,
        description: str | None = None,
    ) -> None:
        payload: dict[str, Any] = {}
        if name is not None:
            payload["name"] = name
        if public is not None:
            payload["public"] = public
        if collaborative is not None:
            payload["collaborative"] = collaborative
        if description is not None:
            payload["description"] = description
        await self._http.put(f"/playlists/{playlist_id}", payload=payload)

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
            await self._http.post(f"/playlists/{playlist_id}/items", payload=payload)
            or {}
        )
        return data.get("snapshot_id") if isinstance(data, dict) else None

    async def replace(self, playlist_id: str, uris: Iterable[str]) -> str | None:
        items = coalesce_items(uris)
        path = f"/playlists/{playlist_id}/items"
        data = await self._http.put(
            path,
            payload={"uris": items[:_MAX_ITEMS_PER_REQUEST]},
        )

        for offset in range(_MAX_ITEMS_PER_REQUEST, len(items), _MAX_ITEMS_PER_REQUEST):
            data = await self._http.post(
                path,
                payload={"uris": items[offset : offset + _MAX_ITEMS_PER_REQUEST]},
            )

        return data.get("snapshot_id") if isinstance(data, dict) else None

    async def remove(self, playlist_id: str, uris: Iterable[str]) -> str | None:
        payload = {"items": [{"uri": uri} for uri in coalesce_items(uris)]}
        data = (
            await self._http.delete(f"/playlists/{playlist_id}/items", payload=payload)
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
            await self._http.put(
                f"/playlists/{playlist_id}/items", payload=payload, retry_safe=False
            )
            or {}
        )
        return data.get("snapshot_id") if isinstance(data, dict) else None

    async def cover_image(self, playlist_id: str) -> list[Image]:
        data = (
            await self._http.get(f"/playlists/{playlist_id}/images", require_user=False)
            or []
        )
        if isinstance(data, list):
            return [validate_model(Image, item) for item in data]
        return []
