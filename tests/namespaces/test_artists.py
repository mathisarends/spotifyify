import unittest
from unittest.mock import AsyncMock

from tests.conftest import artist, paging, track
from spotifyify.namespaces.artists import Artists
from spotifyify.schemas import Artist, PagingArtist, PagingArtistDiscographyAlbum, Track


class TestArtists(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        self.http = AsyncMock()
        self.artists = Artists(self.http)

    async def test_find(self):
        self.http.get.return_value = {"artists": paging()}
        result = await self.artists.find("Radiohead")
        self.assertIsInstance(result, PagingArtist)
        self.http.get.assert_called_once_with(
            "/search",
            params={"q": "Radiohead", "type": "artist", "limit": 10, "offset": 0},
            require_user=False,
        )

    async def test_get(self):
        self.http.get.return_value = artist(id="x", name="Artist")
        result = await self.artists.get("x")
        self.assertIsInstance(result, Artist)

    async def test_get_many(self):
        self.http.get.return_value = {"artists": [artist(id="a", name="A")]}
        result = await self.artists.get_many(["a"])
        self.assertEqual(len(result), 1)

    async def test_top_tracks(self):
        self.http.get.return_value = {"tracks": [track(id="t1", name="Hit")]}
        result = await self.artists.top_tracks("x")
        self.assertEqual(len(result), 1)
        self.assertIsInstance(result[0], Track)
        call_kwargs = self.http.get.call_args
        self.assertEqual(call_kwargs.kwargs["params"], {"market": "US"})

    async def test_top_tracks_custom_market(self):
        self.http.get.return_value = {"tracks": []}
        await self.artists.top_tracks("x", market="JP")
        call_kwargs = self.http.get.call_args
        self.assertEqual(call_kwargs.kwargs["params"], {"market": "JP"})

    async def test_albums(self):
        self.http.get.return_value = paging()
        result = await self.artists.albums("x", include_groups="album,single")
        self.assertIsInstance(result, PagingArtistDiscographyAlbum)
        call_kwargs = self.http.get.call_args
        self.assertEqual(call_kwargs.kwargs["params"]["include_groups"], "album,single")

    async def test_related(self):
        self.http.get.return_value = {"artists": [artist(id="r1", name="Related")]}
        result = await self.artists.related("x")
        self.assertEqual(len(result), 1)
        self.assertIsInstance(result[0], Artist)
