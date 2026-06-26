import unittest
from unittest.mock import AsyncMock

from tests.conftest import paging, track
from spotifyify.namespaces.tracks import Tracks
from spotifyify.schemas import PagingTrack, Track


class TestTracks(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        self.http = AsyncMock()
        self.tracks = Tracks(self.http)

    async def test_find(self):
        self.http.get.return_value = {"tracks": paging()}
        result = await self.tracks.find("test query", limit=10)
        self.assertIsInstance(result, PagingTrack)
        self.http.get.assert_called_once_with(
            "/search",
            params={"q": "test query", "type": "track", "limit": 10, "offset": 0},
            require_user=False,
        )

    async def test_find_with_market(self):
        self.http.get.return_value = {"tracks": paging()}
        await self.tracks.find("q", market="US")
        call_kwargs = self.http.get.call_args
        self.assertEqual(call_kwargs.kwargs["params"]["market"], "US")

    async def test_find_accepts_null_paging_links(self):
        self.http.get.return_value = {
            "tracks": paging(previous=None, next=None),
        }
        result = await self.tracks.find("test query")
        self.assertIsNone(result.previous)
        self.assertIsNone(result.next)

    async def test_get(self):
        self.http.get.return_value = track(id="abc123", name="Test Track")
        result = await self.tracks.get("abc123")
        self.assertIsInstance(result, Track)
        self.http.get.assert_called_once_with(
            "/tracks/abc123",
            params=None,
            require_user=False,
        )

    async def test_get_with_market(self):
        self.http.get.return_value = track(id="abc123", name="Test")
        await self.tracks.get("abc123", market="DE")
        call_kwargs = self.http.get.call_args
        self.assertEqual(call_kwargs.kwargs["params"], {"market": "DE"})

    async def test_get_many(self):
        self.http.get.return_value = {
            "tracks": [track(id="a", name="A"), track(id="b", name="B")]
        }
        result = await self.tracks.get_many(["a", "b"])
        self.assertEqual(len(result), 2)
        self.assertIsInstance(result[0], Track)

    async def test_get_many_filters_none(self):
        self.http.get.return_value = {"tracks": [track(id="a"), None]}
        result = await self.tracks.get_many(["a", "b"])
        self.assertEqual(len(result), 1)
