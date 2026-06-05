import unittest
from unittest.mock import AsyncMock

import httpx
from pydantic import BaseModel

from spotifyify.client import SpotifyClient
from spotifyify.http.auth_context import current_access_token
from spotifyify.http.retry_policy import HttpMethod
from spotifyify.http.transport import HttpTransport


class TestSpotifyClient(unittest.IsolatedAsyncioTestCase):
    def _make_client(self):
        token_provider = AsyncMock()
        token_provider.get_access_token.return_value = "fake-token"
        client = SpotifyClient(
            token_provider=token_provider,
            scopes=["user-read-playback-state"],
            base_url="https://api.spotify.com/v1",
        )
        client._transport = AsyncMock(spec=HttpTransport)
        return client, token_provider

    async def test_open_delegates_to_transport(self):
        client, _ = self._make_client()

        await client.open()

        client._transport.open.assert_awaited_once()

    async def test_close_delegates_to_transport(self):
        client, _ = self._make_client()

        await client.close()

        client._transport.close.assert_awaited_once()

    async def test_context_manager_closes_transport(self):
        client, _ = self._make_client()

        async with client:
            pass

        client._transport.close.assert_awaited_once()

    async def test_get_adds_token_serializes_params_and_parses_response(self):
        client, token_provider = self._make_client()
        client._transport.request.return_value = httpx.Response(
            200, json={"tracks": []}
        )

        result = await client.get(
            "/tracks",
            params={"offset": None},
            require_user=False,
            headers={"X-Test": "value"},
        )

        self.assertEqual(result, {"tracks": []})
        token_provider.get_access_token.assert_awaited_once_with(
            require_user=False,
            scope=["user-read-playback-state"],
        )
        client._transport.request.assert_awaited_once_with(
            HttpMethod.GET,
            "/tracks",
            headers={"Authorization": "Bearer fake-token", "X-Test": "value"},
            params={},
            json=None,
            content=None,
        )

    async def test_post_sends_serialized_payload(self):
        class Payload(BaseModel):
            name: str
            description: str | None = None

        client, _ = self._make_client()
        client._transport.request.return_value = httpx.Response(204)

        await client.post("/playlists", payload=Payload(name="test"))

        client._transport.request.assert_awaited_once_with(
            HttpMethod.POST,
            "/playlists",
            headers={"Authorization": "Bearer fake-token"},
            params=None,
            json={"name": "test"},
            content=None,
        )

    async def test_request_uses_context_access_token_without_provider(self):
        client, token_provider = self._make_client()
        client._transport.request.return_value = httpx.Response(200, json={"ok": True})

        token = current_access_token.set("user-token")
        try:
            result = await client.get("/me", require_user=False)
        finally:
            current_access_token.reset(token)

        self.assertEqual(result, {"ok": True})
        token_provider.get_access_token.assert_not_awaited()
        client._transport.request.assert_awaited_once_with(
            HttpMethod.GET,
            "/me",
            headers={"Authorization": "Bearer user-token"},
            params=None,
            json=None,
            content=None,
        )
