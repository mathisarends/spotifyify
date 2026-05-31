import unittest
from unittest.mock import AsyncMock, MagicMock, patch

import httpx
from pydantic import BaseModel

from spotifyify.client import SpotifyClient, QueryParams, parse_response
from spotifyify.exceptions import SpotifyAPIError


class TestParseResponse(unittest.TestCase):
    def _make_response(self, status_code, json_data=None, content=b"", text=""):
        resp = MagicMock(spec=httpx.Response)
        resp.status_code = status_code
        resp.content = content
        resp.text = text
        if json_data is not None:
            resp.json.return_value = json_data
            resp.content = b'{"data": true}'
        else:
            resp.json.side_effect = ValueError("No JSON")
        return resp

    def test_204_returns_none(self):
        resp = self._make_response(204)
        self.assertIsNone(parse_response(resp))

    def test_empty_content_returns_none(self):
        resp = self._make_response(200, content=b"")
        resp.json.side_effect = ValueError
        self.assertIsNone(parse_response(resp))

    def test_200_with_json(self):
        resp = self._make_response(200, json_data={"tracks": []})
        result = parse_response(resp)
        self.assertEqual(result, {"tracks": []})

    def test_400_raises_spotify_api_error_with_error_object(self):
        resp = self._make_response(
            400,
            json_data={"error": {"message": "bad request"}},
        )
        with self.assertRaises(SpotifyAPIError) as ctx:
            parse_response(resp)
        self.assertEqual(ctx.exception.status_code, 400)
        self.assertEqual(ctx.exception.message, "bad request")

    def test_400_raises_with_plain_message(self):
        resp = self._make_response(400)
        resp.text = "server error"
        with self.assertRaises(SpotifyAPIError) as ctx:
            parse_response(resp)
        self.assertEqual(ctx.exception.message, "server error")

    def test_400_with_non_dict_error(self):
        resp = self._make_response(400, json_data={"error": "simple string"})
        with self.assertRaises(SpotifyAPIError) as ctx:
            parse_response(resp)
        self.assertEqual(ctx.exception.message, "simple string")


class TestDumpParams(unittest.TestCase):
    def test_none_returns_none(self):
        self.assertIsNone(SpotifyClient._dump_params(None))

    def test_dict_input(self):
        result = SpotifyClient._dump_params({"limit": 10, "offset": None})
        self.assertEqual(result, {"limit": 10})

    def test_pydantic_model_input(self):
        params = QueryParams(limit=5)
        result = SpotifyClient._dump_params(params)
        self.assertEqual(result, {"limit": 5})


class TestDumpPayload(unittest.TestCase):
    def test_none_returns_none(self):
        self.assertIsNone(SpotifyClient._dump_payload(None))

    def test_dict_passthrough(self):
        d = {"name": "test"}
        self.assertIs(SpotifyClient._dump_payload(d), d)

    def test_list_passthrough(self):
        lst = [1, 2, 3]
        self.assertIs(SpotifyClient._dump_payload(lst), lst)

    def test_string_passthrough(self):
        self.assertIs(SpotifyClient._dump_payload("hello"), "hello")

    def test_pydantic_model(self):
        class Payload(BaseModel):
            name: str

        payload = Payload(name="test")
        result = SpotifyClient._dump_payload(payload)
        self.assertEqual(result, {"name": "test"})


class TestSpotifyClientLifecycle(unittest.IsolatedAsyncioTestCase):
    def _make_client(self, **kwargs):
        token_provider = AsyncMock()
        token_provider.get_access_token.return_value = "fake-token"
        return SpotifyClient(
            token_provider=token_provider,
            scopes=["user-read-playback-state"],
            base_url="https://api.spotify.com/v1",
            **kwargs,
        )

    def test_negative_max_retries_raises(self):
        with self.assertRaises(ValueError):
            self._make_client(max_retries=-1)

    def test_negative_retry_backoff_raises(self):
        with self.assertRaises(ValueError):
            self._make_client(retry_backoff_seconds=-1)

    async def test_open_creates_httpx_client(self):
        client = self._make_client()
        self.assertIsNone(client._client)
        await client.open()
        self.assertIsNotNone(client._client)
        await client.close()

    async def test_close_sets_client_to_none(self):
        client = self._make_client()
        await client.open()
        await client.close()
        self.assertIsNone(client._client)

    async def test_close_idempotent(self):
        client = self._make_client()
        await client.close()  # should not raise

    async def test_context_manager(self):
        client = self._make_client()
        async with client:
            pass
        self.assertIsNone(client._client)


class TestSpotifyClientRetries(unittest.IsolatedAsyncioTestCase):
    def _make_client(self, **kwargs):
        token_provider = AsyncMock()
        token_provider.get_access_token.return_value = "fake-token"
        client = SpotifyClient(
            token_provider=token_provider,
            scopes=[],
            base_url="https://api.spotify.com/v1",
            **kwargs,
        )
        client._client = AsyncMock(spec=httpx.AsyncClient)
        return client

    async def test_get_retries_server_error_with_exponential_backoff(self):
        client = self._make_client()
        client._client.request.side_effect = [
            httpx.Response(503, json={"error": {"message": "unavailable"}}),
            httpx.Response(200, json={"tracks": []}),
        ]

        with patch("spotifyify.client.asyncio.sleep", new_callable=AsyncMock) as sleep:
            result = await client.get("/playlists/test/tracks")

        self.assertEqual(result, {"tracks": []})
        self.assertEqual(client._client.request.await_count, 2)
        sleep.assert_awaited_once_with(1.0)

    async def test_rate_limit_retries_post_and_honors_retry_after(self):
        client = self._make_client()
        client._client.request.side_effect = [
            httpx.Response(
                429,
                headers={"Retry-After": "2.5"},
                json={"error": {"message": "rate limited"}},
            ),
            httpx.Response(204),
        ]

        with patch("spotifyify.client.asyncio.sleep", new_callable=AsyncMock) as sleep:
            result = await client.post("/playlists/test/tracks", payload={"uris": []})

        self.assertIsNone(result)
        self.assertEqual(client._client.request.await_count, 2)
        sleep.assert_awaited_once_with(2.5)

    async def test_post_does_not_retry_server_error(self):
        client = self._make_client()
        client._client.request.return_value = httpx.Response(
            503, json={"error": {"message": "unavailable"}}
        )

        with patch("spotifyify.client.asyncio.sleep", new_callable=AsyncMock) as sleep:
            with self.assertRaises(SpotifyAPIError):
                await client.post("/playlists/test/tracks", payload={"uris": []})

        client._client.request.assert_awaited_once()
        sleep.assert_not_awaited()

    async def test_retryable_error_is_raised_after_retry_budget_is_exhausted(self):
        client = self._make_client(max_retries=2, retry_backoff_seconds=0.25)
        client._client.request.return_value = httpx.Response(
            503, json={"error": {"message": "unavailable"}}
        )

        with patch("spotifyify.client.asyncio.sleep", new_callable=AsyncMock) as sleep:
            with self.assertRaises(SpotifyAPIError):
                await client.get("/playlists/test/tracks")

        self.assertEqual(client._client.request.await_count, 3)
        self.assertEqual(
            [call.args for call in sleep.await_args_list], [(0.25,), (0.5,)]
        )
