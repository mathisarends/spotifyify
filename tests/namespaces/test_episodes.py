import unittest
from unittest.mock import AsyncMock

from spotifyify.config import ApiMode
from spotifyify.namespaces.episodes import Episodes
from spotifyify.schemas import Episode, PagingSimplifiedEpisode
from tests.conftest import episode, paging


class TestEpisodes(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        self.http = AsyncMock()
        self.http.api_mode = ApiMode.EXTENDED
        self.http.concurrency = 8
        self.episodes = Episodes(self.http)

    async def test_find(self):
        self.http.get.return_value = {"episodes": paging()}
        result = await self.episodes.find("interview")
        self.assertIsInstance(result, PagingSimplifiedEpisode)

    async def test_get(self):
        self.http.get.return_value = episode(id="e1", name="Episode 1")
        result = await self.episodes.get("e1")
        self.assertIsInstance(result, Episode)

    async def test_get_with_market(self):
        self.http.get.return_value = episode(id="e1", name="Episode 1")
        await self.episodes.get("e1", market="DE")
        call_kwargs = self.http.get.call_args
        self.assertEqual(call_kwargs.kwargs["params"], {"market": "DE"})

    async def test_get_many(self):
        self.http.get.return_value = {
            "episodes": [episode(id="e1", name="Ep1"), episode(id="e2", name="Ep2")]
        }
        result = await self.episodes.get_many(["e1", "e2"])
        self.assertEqual(len(result), 2)
        self.assertIsInstance(result[0], Episode)

    async def test_get_many_preserves_missing_positions(self):
        self.http.get.return_value = {"episodes": [None, episode(id="e1", name="Ep1")]}
        result = await self.episodes.get_many(["e1", "e2"])
        self.assertEqual(len(result), 2)
        self.assertIsNone(result[0])
