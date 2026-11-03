from collections.abc import AsyncIterator
from typing import Any
from spotifyify.pagination import iter_cursor_items
from spotifyify.schemas import PlayHistory
from spotifyify.validation import spotify_id as validate_id
from spotifyify.validation import integer as validate_integer
from spotifyify.validation import market as validate_market
from spotifyify.validation import playback_offset as validate_offset
from spotifyify.validation import page as validate_page
from spotifyify.validation import uri as validate_uri
from spotifyify.utils import coalesce_items
from spotifyify.http.response import validate_model

from spotifyify.client import SpotifyAPIClient
from spotifyify.schemas import (
    CursorPagingPlayHistory,
    Device,
    PlaybackState,
    PlayerQueue,
)


class Player:
    def __init__(self, http: SpotifyAPIClient) -> None:
        self._http = http

    async def state(self, *, market: str | None = None) -> PlaybackState | None:
        market = validate_market(market)
        data = await self._http.get(
            "/me/player",
            params={"market": market} if market else None,
        )
        return validate_model(PlaybackState, data) if data else None

    async def play(
        self,
        *,
        device_id: str | None = None,
        context_uri: str | None = None,
        uris: list[str] | None = None,
        offset: dict[str, Any] | None = None,
        position_ms: int | None = None,
    ) -> None:
        if device_id is not None:
            device_id = validate_id(device_id)
        if position_ms is not None:
            validate_integer("position_ms", position_ms)
        if context_uri is not None and uris is not None:
            raise ValueError("context_uri and uris are mutually exclusive")
        if context_uri is not None:
            validate_uri(context_uri, kinds=("album", "artist", "playlist"))
        if uris is not None:
            if not uris:
                raise ValueError("uris must not be empty")
            uris = [validate_uri(value) for value in coalesce_items(uris)]
        if offset is not None:
            validate_offset(offset)
        payload: dict[str, Any] = {}
        if context_uri is not None:
            payload["context_uri"] = context_uri
        if uris is not None:
            payload["uris"] = uris
        if offset is not None:
            payload["offset"] = offset
        if position_ms is not None:
            payload["position_ms"] = position_ms
        await self._http.put(
            "/me/player/play",
            params={"device_id": device_id} if device_id else None,
            payload=payload,
        )

    async def pause(self, *, device_id: str | None = None) -> None:
        if device_id is not None:
            device_id = validate_id(device_id)
        await self._http.put(
            "/me/player/pause",
            params={"device_id": device_id} if device_id else None,
        )

    async def skip(self, *, device_id: str | None = None) -> None:
        if device_id is not None:
            device_id = validate_id(device_id)
        await self._http.post(
            "/me/player/next",
            params={"device_id": device_id} if device_id else None,
        )

    async def previous(self, *, device_id: str | None = None) -> None:
        if device_id is not None:
            device_id = validate_id(device_id)
        await self._http.post(
            "/me/player/previous",
            params={"device_id": device_id} if device_id else None,
        )

    async def seek(self, position_ms: int, *, device_id: str | None = None) -> None:
        if device_id is not None:
            device_id = validate_id(device_id)
        if position_ms is not None:
            validate_integer("position_ms", position_ms)
        params: dict[str, Any] = {"position_ms": position_ms}
        if device_id:
            params["device_id"] = device_id
        await self._http.put("/me/player/seek", params=params)

    async def repeat(self, state: str, *, device_id: str | None = None) -> None:
        if device_id is not None:
            device_id = validate_id(device_id)
        if state not in {"track", "context", "off"}:
            raise ValueError("repeat state must be track, context, or off")
        params: dict[str, Any] = {"state": state}
        if device_id:
            params["device_id"] = device_id
        await self._http.put("/me/player/repeat", params=params)

    async def shuffle(self, state: bool, *, device_id: str | None = None) -> None:
        if device_id is not None:
            device_id = validate_id(device_id)
        if not isinstance(state, bool):
            raise ValueError("shuffle state must be a boolean")
        params: dict[str, Any] = {"state": state}
        if device_id:
            params["device_id"] = device_id
        await self._http.put("/me/player/shuffle", params=params)

    async def volume(
        self, volume_percent: int, *, device_id: str | None = None
    ) -> None:
        if device_id is not None:
            device_id = validate_id(device_id)
        validate_integer("volume_percent", volume_percent, maximum=100)
        params: dict[str, Any] = {"volume_percent": volume_percent}
        if device_id:
            params["device_id"] = device_id
        await self._http.put("/me/player/volume", params=params)

    async def queue(self) -> PlayerQueue:
        data = await self._http.get("/me/player/queue") or {}
        return validate_model(PlayerQueue, data)

    async def add_to_queue(self, uri: str, *, device_id: str | None = None) -> None:
        if device_id is not None:
            device_id = validate_id(device_id)
        validate_uri(uri)
        params: dict[str, Any] = {"uri": uri}
        if device_id:
            params["device_id"] = device_id
        await self._http.post("/me/player/queue", params=params)

    async def transfer(self, device_id: str, *, play: bool = False) -> None:
        device_id = validate_id(device_id)
        await self._http.put(
            "/me/player",
            payload={"device_ids": [device_id], "play": play},
        )

    async def devices(self) -> list[Device]:
        data = await self._http.get("/me/player/devices") or {}
        return [
            validate_model(Device, item)
            for item in (data.get("devices", []) if isinstance(data, dict) else [])
        ]

    async def recently_played(
        self,
        *,
        limit: int = 20,
        after: int | None = None,
        before: int | None = None,
    ) -> CursorPagingPlayHistory:
        validate_page(limit)
        if after is not None:
            validate_integer("after", after)
        if before is not None:
            validate_integer("before", before)
        if after is not None and before is not None:
            raise ValueError("after and before are mutually exclusive")
        params: dict[str, Any] = {"limit": limit}
        if after is not None:
            params["after"] = after
        if before is not None:
            params["before"] = before
        data = await self._http.get("/me/player/recently-played", params=params) or {}
        return validate_model(CursorPagingPlayHistory, data)

    async def iter_recently_played(
        self, *, limit: int = 50, **kwargs: Any
    ) -> AsyncIterator[PlayHistory]:
        async for item in iter_cursor_items(
            self.recently_played, limit=limit, numeric=True, **kwargs
        ):
            yield item
