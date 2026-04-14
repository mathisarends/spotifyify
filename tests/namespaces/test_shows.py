import unittest
from unittest.mock import AsyncMock

from tests.conftest import paging, show, simplified_show
from spotifyify.namespaces.shows import Shows
from spotifyify.schemas import (
    PagingSimplifiedEpisode,
    PagingSimplifiedShow,
    Show,
    SimplifiedShow,
)


class TestShows(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        self.http = AsyncMock()
        self.shows = Shows(self.http)

    async def test_find(self):
        self.http.get.return_value = {"shows": paging()}
        result = await self.shows.find("podcast")
        self.assertIsInstance(result, PagingSimplifiedShow)

    async def test_get(self):
        self.http.get.return_value = show(id="s1", name="My Show")
        result = await self.shows.get("s1")
        self.assertIsInstance(result, Show)

    async def test_get_many(self):
        self.http.get.return_value = {
            "shows": [
                simplified_show(id="s1", name="Show1"),
                simplified_show(id="s2", name="Show2"),
            ]
        }
        result = await self.shows.get_many(["s1", "s2"])
        self.assertEqual(len(result), 2)
        self.assertIsInstance(result[0], SimplifiedShow)

    async def test_episodes(self):
        self.http.get.return_value = paging()
        result = await self.shows.episodes("s1", market="US")
        self.assertIsInstance(result, PagingSimplifiedEpisode)
        call_kwargs = self.http.get.call_args
        self.assertEqual(call_kwargs.kwargs["params"]["market"], "US")
