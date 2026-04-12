import unittest
from unittest.mock import AsyncMock

from tests.conftest import paging, track
from spotifyify.namespaces.tracks import Tracks
from spotifyify.schemas import AudioFeatures, PagingTrack, Recommendations, Track


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

    async def test_audio_features(self):
        self.http.get.return_value = {
            "audio_features": [{"id": "a", "danceability": 0.8, "energy": 0.6}]
        }
        result = await self.tracks.audio_features(["a"])
        self.assertEqual(len(result), 1)
        self.assertIsInstance(result[0], AudioFeatures)

    async def test_recommendations(self):
        self.http.get.return_value = {"tracks": [], "seeds": []}
        result = await self.tracks.recommendations(seed_genres=["pop"])
        self.assertIsInstance(result, Recommendations)
        call_kwargs = self.http.get.call_args
        self.assertEqual(call_kwargs.kwargs["params"]["seed_genres"], "pop")

    async def test_recommendations_no_seeds(self):
        self.http.get.return_value = {"tracks": [], "seeds": []}
        await self.tracks.recommendations()
        call_kwargs = self.http.get.call_args
        self.assertNotIn("seed_artists", call_kwargs.kwargs["params"])
        self.assertNotIn("seed_tracks", call_kwargs.kwargs["params"])
        self.assertNotIn("seed_genres", call_kwargs.kwargs["params"])
