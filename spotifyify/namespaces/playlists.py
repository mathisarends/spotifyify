from __future__ import annotations

from collections.abc import AsyncIterator
from typing import Any
from spotifyify.pagination import iter_offset_items
from spotifyify.schemas import PlaylistItem, SimplifiedPlaylist

from spotifyify.validation import spotify_id as validate_id
from spotifyify.validation import integer as validate_integer
from spotifyify.validation import market as validate_market
from spotifyify.validation import page as validate_page

from spotifyify.namespaces.base import Resource
from spotifyify.config import ApiMode
from spotifyify.exceptions import SpotifyResponseError, SpotifyBatchError, SpotifyError

from spotifyify.http.response import validate_model

from typing import TYPE_CHECKING

from collections.abc import Iterable

from spotifyify.schemas import (
    Image,
    PagingPlaylist,
    PagingPlaylistTrack,
    Playlist,
    PlaylistProjection,
)
from spotifyify.utils import coalesce_csv, coalesce_items
from spotifyify.batching import chunks
from spotifyify.http.response import object_response
from spotifyify.validation import uri as validate_uri

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
        validate_page(limit, offset)
        return validate_model(
            PagingPlaylist,
            await self._search("playlist", query, limit=limit, offset=offset),
        )

    find = search

    async def get(self, playlist_id: str, *, market: str | None = None) -> Playlist:
        market = validate_market(market)
        playlist_id = validate_id(playlist_id)
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
        validate_page(limit, offset)
        if user_id is not None:
            user_id = validate_id(user_id)
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
        validate_page(limit, offset)
        market = validate_market(market)
        playlist_id = validate_id(playlist_id)
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
        if user_id is not None:
            user_id = validate_id(user_id)
        if not name.strip():
            raise ValueError("Playlist name must not be empty")
        if public and collaborative:
            raise ValueError("Collaborative playlists must be private")
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
        playlist_id = validate_id(playlist_id)
        if all(value is None for value in (name, public, collaborative, description)):
            raise ValueError("Supply at least one playlist detail to update")
        if public and collaborative:
            raise ValueError("Collaborative playlists must be private")
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
        self, playlist_id: str, uris: Iterable[str], *, position: int | None = None
    ) -> str | None:
        playlist_id = validate_id(playlist_id)
        if position is not None:
            validate_integer("position", position)
        values = [validate_uri(value) for value in coalesce_items(uris)]
        return await self._write_batches("add", playlist_id, values, position=position)

    async def replace(self, playlist_id: str, uris: Iterable[str]) -> str | None:
        playlist_id = validate_id(playlist_id)
        values = [validate_uri(value) for value in coalesce_items(uris)]
        return await self._write_batches("replace", playlist_id, values)

    async def remove(
        self, playlist_id: str, uris: Iterable[str], *, snapshot_id: str | None = None
    ) -> str | None:
        playlist_id = validate_id(playlist_id)
        if snapshot_id is not None:
            snapshot_id = validate_id(snapshot_id)
        values = [validate_uri(value) for value in coalesce_items(uris)]
        return await self._write_batches(
            "remove", playlist_id, values, snapshot_id=snapshot_id
        )

    async def reorder(
        self,
        playlist_id: str,
        *,
        range_start: int,
        insert_before: int,
        range_length: int = 1,
        snapshot_id: str | None = None,
    ) -> str | None:
        playlist_id = validate_id(playlist_id)
        if snapshot_id is not None:
            snapshot_id = validate_id(snapshot_id)
        if range_start is not None:
            validate_integer("range_start", range_start)
        if insert_before is not None:
            validate_integer("insert_before", insert_before)
        validate_integer("range_length", range_length, minimum=1)
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
        playlist_id = validate_id(playlist_id)
        data = (
            await self._http.get(f"/playlists/{playlist_id}/images", require_user=False)
            or []
        )
        if isinstance(data, list):
            return [validate_model(Image, item) for item in data]
        return []

    async def _write_batches(
        self,
        operation: str,
        playlist_id: str,
        values: list[str],
        *,
        position: int | None = None,
        snapshot_id: str | None = None,
    ) -> str | None:
        batches = chunks(values, _MAX_ITEMS_PER_REQUEST)
        if operation == "replace" and not batches:
            batches = [[]]
        completed = 0
        snapshot = snapshot_id
        path = f"/playlists/{playlist_id}/items"
        for index, batch in enumerate(batches):
            payload: dict[str, Any] = {"uris": batch}
            if operation == "remove":
                payload = {"items": [{"uri": value} for value in batch]}
                if snapshot:
                    payload["snapshot_id"] = snapshot
                action = self._http.delete
            elif operation == "replace" and index == 0:
                action = self._http.put
            else:
                action = self._http.post
                if position is not None:
                    payload["position"] = position + completed
            try:
                response = object_response(await action(path, payload=payload))
                next_snapshot = response.get("snapshot_id")
                if not isinstance(next_snapshot, str) or not next_snapshot:
                    raise SpotifyResponseError(
                        "Playlist write response is missing snapshot_id"
                    )
                snapshot = next_snapshot
            except SpotifyError as exc:
                if completed:
                    raise SpotifyBatchError(
                        operation,
                        completed_items=completed,
                        total_items=len(values),
                        snapshot_id=snapshot,
                    ) from exc
                raise
            completed += len(batch)
        return snapshot

    async def iter_search(
        self, query: str, *, limit: int = 10, offset: int = 0, **kwargs: Any
    ) -> AsyncIterator[SimplifiedPlaylist | None]:
        """Yield results across pages, stopping without prefetch when the caller stops."""
        async for item in iter_offset_items(
            self.search, limit=limit, offset=offset, query=query, **kwargs
        ):
            yield item

    async def iter_items(
        self, playlist_id: str, *, limit: int = 50, offset: int = 0, **kwargs: Any
    ) -> AsyncIterator[PlaylistItem]:
        """Yield results across pages, stopping without prefetch when the caller stops."""
        async for item in iter_offset_items(
            self.items, limit=limit, offset=offset, playlist_id=playlist_id, **kwargs
        ):
            yield item

    async def iter_list(
        self, *, limit: int = 50, offset: int = 0, **kwargs: Any
    ) -> AsyncIterator[SimplifiedPlaylist | None]:
        """Yield results across pages, stopping without prefetch when the caller stops."""
        async for item in iter_offset_items(
            self.list, limit=limit, offset=offset, **kwargs
        ):
            yield item
