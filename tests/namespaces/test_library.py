import unittest
from unittest.mock import AsyncMock

from tests.conftest import paging
from spotifyify.namespaces.library import Library
from spotifyify.schemas import (
    PagingArtist,
    PagingSavedAlbum,
    PagingSavedEpisode,
    PagingSavedShow,
    PagingSavedTrack,
    PagingTrack,
)


class TestLibrary(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        self.http = AsyncMock()
        self.library = Library(self.http)

    async def test_saved_tracks(self):
        self.http.get.return_value = paging()
        result = await self.library.saved_tracks()
        self.assertIsInstance(result, PagingSavedTrack)
        self.http.get.assert_called_once()

    async def test_saved_albums(self):
        self.http.get.return_value = paging()
        result = await self.library.saved_albums()
        self.assertIsInstance(result, PagingSavedAlbum)

    async def test_saved_shows(self):
        self.http.get.return_value = paging()
        result = await self.library.saved_shows()
        self.assertIsInstance(result, PagingSavedShow)

    async def test_saved_episodes(self):
        self.http.get.return_value = paging()
        result = await self.library.saved_episodes()
        self.assertIsInstance(result, PagingSavedEpisode)

    async def test_save_tracks(self):
        self.http.put.return_value = None
        await self.library.save_tracks(["id1", "id2"])
        self.http.put.assert_called_once_with("/me/tracks", params={"ids": "id1,id2"})

    async def test_remove_tracks(self):
        self.http.delete.return_value = None
        await self.library.remove_tracks(["id1"])
        self.http.delete.assert_called_once_with("/me/tracks", params={"ids": "id1"})

    async def test_save_albums(self):
        self.http.put.return_value = None
        await self.library.save_albums(["a1"])
        self.http.put.assert_called_once_with("/me/albums", params={"ids": "a1"})

    async def test_remove_albums(self):
        self.http.delete.return_value = None
        await self.library.remove_albums(["a1"])
        self.http.delete.assert_called_once_with("/me/albums", params={"ids": "a1"})

    async def test_save_shows(self):
        self.http.put.return_value = None
        await self.library.save_shows(["s1"])
        self.http.put.assert_called_once_with("/me/shows", params={"ids": "s1"})

    async def test_remove_shows(self):
        self.http.delete.return_value = None
        await self.library.remove_shows(["s1"])
        self.http.delete.assert_called_once_with("/me/shows", params={"ids": "s1"})

    async def test_save_episodes(self):
        self.http.put.return_value = None
        await self.library.save_episodes(["e1"])
        self.http.put.assert_called_once_with("/me/episodes", params={"ids": "e1"})

    async def test_remove_episodes(self):
        self.http.delete.return_value = None
        await self.library.remove_episodes(["e1"])
        self.http.delete.assert_called_once_with("/me/episodes", params={"ids": "e1"})

    async def test_check_tracks(self):
        self.http.get.return_value = [True, False]
        result = await self.library.check_tracks(["id1", "id2"])
        self.assertEqual(result, [True, False])

    async def test_check_albums(self):
        self.http.get.return_value = [True]
        result = await self.library.check_albums(["a1"])
        self.assertEqual(result, [True])

    async def test_check_shows(self):
        self.http.get.return_value = [False]
        result = await self.library.check_shows(["s1"])
        self.assertEqual(result, [False])

    async def test_check_episodes(self):
        self.http.get.return_value = [True]
        result = await self.library.check_episodes(["e1"])
        self.assertEqual(result, [True])

    async def test_check_returns_empty_for_non_list(self):
        self.http.get.return_value = None
        result = await self.library.check_tracks(["id1"])
        self.assertEqual(result, [])

    async def test_top_tracks(self):
        self.http.get.return_value = paging()
        result = await self.library.top_tracks(time_range="short_term")
        self.assertIsInstance(result, PagingTrack)

    async def test_top_artists(self):
        self.http.get.return_value = paging()
        result = await self.library.top_artists()
        self.assertIsInstance(result, PagingArtist)
