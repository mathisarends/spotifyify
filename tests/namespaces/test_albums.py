import unittest
from unittest.mock import AsyncMock

from tests.conftest import album, paging
from spotifyify.namespaces.albums import Albums
from spotifyify.schemas import Album, PagingSimplifiedAlbum, PagingSimplifiedTrack


class TestAlbums(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        self.http = AsyncMock()
        self.albums = Albums(self.http)

    async def test_find(self):
        self.http.get.return_value = {"albums": paging()}
        result = await self.albums.find("test")
        self.assertIsInstance(result, PagingSimplifiedAlbum)
        self.http.get.assert_called_once_with(
            "/search",
            params={"q": "test", "type": "album", "limit": 10, "offset": 0},
            require_user=False,
        )

    async def test_get(self):
        self.http.get.return_value = album(id="abc")
        result = await self.albums.get("abc")
        self.assertIsInstance(result, Album)

    async def test_get_with_market(self):
        self.http.get.return_value = album(id="abc")
        await self.albums.get("abc", market="US")
        call_kwargs = self.http.get.call_args
        self.assertEqual(call_kwargs.kwargs["params"], {"market": "US"})

    async def test_get_many(self):
        self.http.get.return_value = {
            "albums": [album(id="a", name="A"), album(id="b", name="B")]
        }
        result = await self.albums.get_many(["a", "b"])
        self.assertEqual(len(result), 2)
        self.assertIsInstance(result[0], Album)

    async def test_tracks(self):
        self.http.get.return_value = paging()
        result = await self.albums.tracks("abc")
        self.assertIsInstance(result, PagingSimplifiedTrack)
        self.http.get.assert_called_once_with(
            "/albums/abc/tracks",
            params={"limit": 50, "offset": 0},
            require_user=False,
        )

    async def test_new_releases(self):
        self.http.get.return_value = {"albums": paging()}
        result = await self.albums.new_releases(country="SE")
        self.assertIsInstance(result, PagingSimplifiedAlbum)
        call_kwargs = self.http.get.call_args
        self.assertEqual(call_kwargs.kwargs["params"]["country"], "SE")
