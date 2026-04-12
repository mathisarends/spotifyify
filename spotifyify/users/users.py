from __future__ import annotations

from typing import TYPE_CHECKING, Any

from spotifyify.http.client import SpotifyAPIHttpClient

if TYPE_CHECKING:
    from spotifyify.spotifyify import Spotifyify


class UsersNamespace:
    def __init__(self, client: Spotifyify) -> None:
        self._client = client

    @property
    def http(self) -> SpotifyAPIHttpClient:
        return self._client.http

    async def get_current(self) -> dict[str, Any]:
        data = await self.http.get("/me")
        return data if isinstance(data, dict) else {}

    async def get_profile(self, user_id: str) -> dict[str, Any]:
        data = await self.http.get(f"/users/{user_id}", require_user=False)
        return data if isinstance(data, dict) else {}
