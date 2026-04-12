from __future__ import annotations

from typing import TYPE_CHECKING, Any

from spotifyify.http.client import SpotifyAPIHttpClient
from spotifyify.schemas import Device, PlaybackState, Queue

if TYPE_CHECKING:
    from spotifyify.spotifyify import Spotifyify


class PlayerNamespace:
    def __init__(self, client: Spotifyify) -> None:
        self._client = client

    @property
    def http(self) -> SpotifyAPIHttpClient:
        return self._client.http

    async def state(self, *, market: str | None = None) -> PlaybackState | None:
        data = await self.http.get(
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
        await self.http.put(
            "/me/player/play",
            params={"device_id": device_id} if device_id else None,
            payload=payload,
        )

    async def pause(self, *, device_id: str | None = None) -> None:
        await self.http.put(
            "/me/player/pause",
            params={"device_id": device_id} if device_id else None,
        )

    async def skip(self, *, device_id: str | None = None) -> None:
        await self.http.post(
            "/me/player/next",
            params={"device_id": device_id} if device_id else None,
        )

    async def queue(self) -> Queue:
        data = await self.http.get("/me/player/queue") or {}
        return Queue.model_validate(data)

    async def add_to_queue(self, uri: str, *, device_id: str | None = None) -> None:
        params = {"uri": uri}
        if device_id:
            params["device_id"] = device_id
        await self.http.post("/me/player/queue", params=params)

    async def devices(self) -> list[Device]:
        data = await self.http.get("/me/player/devices") or {}
        return [Device.model_validate(item) for item in data.get("devices", [])]

    async def volume(
        self, volume_percent: int, *, device_id: str | None = None
    ) -> None:
        params = {"volume_percent": volume_percent}
        if device_id:
            params["device_id"] = device_id
        await self.http.put("/me/player/volume", params=params)
