import unittest
from unittest.mock import AsyncMock, MagicMock

import httpx

from spotifyify.client import SpotifyClient, QueryParams, RequestPayload, parse_response
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
        payload = RequestPayload(name="test")
        result = SpotifyClient._dump_payload(payload)
        self.assertEqual(result, {"name": "test"})

    def test_invalid_type_raises(self):
        with self.assertRaises(TypeError):
            SpotifyClient._dump_payload(42)


class TestSpotifyClientLifecycle(unittest.IsolatedAsyncioTestCase):
    def _make_client(self):
        token_provider = AsyncMock()
        token_provider.get_access_token.return_value = "fake-token"
        return SpotifyClient(
            token_provider=token_provider,
            scopes=["user-read-playback-state"],
            base_url="https://api.spotify.com/v1",
        )

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
