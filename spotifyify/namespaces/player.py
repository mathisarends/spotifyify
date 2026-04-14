from typing import Any

from spotifyify.client import SpotifyClient
from spotifyify.schemas import (
    CursorPagingPlayHistory,
    Device,
    PlaybackState,
    PlayerQueue,
)


class Player:
    def __init__(self, http: SpotifyClient) -> None:
        self._http = http

    async def state(self, *, market: str | None = None) -> PlaybackState | None:
        data = await self._http.get(
            "/me/player",
            params={"market": market} if market else None,
        )
        return PlaybackState.model_validate(data) if data else None

    async def play(
        self,
        *,
        device_id: str | None = None,
        context_uri: str | None = None,
        uris: list[str] | None = None,
        offset: dict[str, Any] | None = None,
        position_ms: int | None = None,
    ) -> None:
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
        await self._http.put(
            "/me/player/pause",
            params={"device_id": device_id} if device_id else None,
        )

    async def skip(self, *, device_id: str | None = None) -> None:
        await self._http.post(
            "/me/player/next",
            params={"device_id": device_id} if device_id else None,
        )

    async def previous(self, *, device_id: str | None = None) -> None:
        await self._http.post(
            "/me/player/previous",
            params={"device_id": device_id} if device_id else None,
        )

    async def seek(self, position_ms: int, *, device_id: str | None = None) -> None:
        params: dict[str, Any] = {"position_ms": position_ms}
        if device_id:
            params["device_id"] = device_id
        await self._http.put("/me/player/seek", params=params)

    async def repeat(self, state: str, *, device_id: str | None = None) -> None:
        params: dict[str, Any] = {"state": state}
        if device_id:
            params["device_id"] = device_id
        await self._http.put("/me/player/repeat", params=params)

    async def shuffle(self, state: bool, *, device_id: str | None = None) -> None:
        params: dict[str, Any] = {"state": state}
        if device_id:
            params["device_id"] = device_id
        await self._http.put("/me/player/shuffle", params=params)

    async def volume(
        self, volume_percent: int, *, device_id: str | None = None
    ) -> None:
        params: dict[str, Any] = {"volume_percent": volume_percent}
        if device_id:
            params["device_id"] = device_id
        await self._http.put("/me/player/volume", params=params)

    async def queue(self) -> PlayerQueue:
        data = await self._http.get("/me/player/queue") or {}
        return PlayerQueue.model_validate(data)

    async def add_to_queue(self, uri: str, *, device_id: str | None = None) -> None:
        params: dict[str, Any] = {"uri": uri}
        if device_id:
            params["device_id"] = device_id
        await self._http.post("/me/player/queue", params=params)

    async def transfer(self, device_id: str, *, play: bool = False) -> None:
        await self._http.put(
            "/me/player",
            payload={"device_ids": [device_id], "play": play},
        )

    async def devices(self) -> list[Device]:
        data = await self._http.get("/me/player/devices") or {}
        return [
            Device.model_validate(item)
            for item in (data.get("devices", []) if isinstance(data, dict) else [])
        ]

    async def recently_played(
        self,
        *,
        limit: int = 20,
        after: int | None = None,
        before: int | None = None,
    ) -> CursorPagingPlayHistory:
        params: dict[str, Any] = {"limit": limit}
        if after is not None:
            params["after"] = after
        if before is not None:
            params["before"] = before
        data = await self._http.get("/me/player/recently-played", params=params) or {}
        return CursorPagingPlayHistory.model_validate(data)
