import unittest
from unittest.mock import AsyncMock, MagicMock

from tests.conftest import paging, playlist
from spotifyify.namespaces.playlists import Playlists
from spotifyify.schemas import Image, PagingPlaylist, Playlist


class TestPlaylists(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        self.http = AsyncMock()
        self.mock_client = MagicMock()
        self.mock_client.http = self.http
        self.playlists = Playlists(self.mock_client)

    async def test_find(self):
        self.http.get.return_value = {"playlists": paging()}
        result = await self.playlists.find("chill")
        self.assertIsInstance(result, PagingPlaylist)
        self.http.get.assert_called_once_with(
            "/search",
            params={"q": "chill", "type": "playlist", "limit": 10, "offset": 0},
            require_user=False,
        )

    async def test_get(self):
        self.http.get.return_value = playlist(id="p1", name="My Playlist")
        result = await self.playlists.get("p1")
        self.assertIsInstance(result, Playlist)

    async def test_list_current_user(self):
        self.http.get.return_value = paging()
        result = await self.playlists.list()
        self.assertIsInstance(result, PagingPlaylist)
        call_args = self.http.get.call_args
        self.assertEqual(call_args.args[0], "/me/playlists")

    async def test_list_specific_user(self):
        self.http.get.return_value = paging()
        await self.playlists.list(user_id="user123")
        call_args = self.http.get.call_args
        self.assertEqual(call_args.args[0], "/users/user123/playlists")

    async def test_create(self):
        mock_users = AsyncMock()
        mock_users.me.return_value = MagicMock(id="me123")
        self.mock_client.users = mock_users

        self.http.post.return_value = playlist(id="new_p", name="New Playlist")
        result = await self.playlists.create("New Playlist", public=True)
        self.assertIsInstance(result, Playlist)
        call_args = self.http.post.call_args
        self.assertEqual(call_args.args[0], "/users/me123/playlists")

    async def test_create_with_user_id(self):
        self.http.post.return_value = playlist(id="new_p", name="New Playlist")
        await self.playlists.create("New Playlist", user_id="other_user")
        call_args = self.http.post.call_args
        self.assertEqual(call_args.args[0], "/users/other_user/playlists")

    async def test_update(self):
        self.http.put.return_value = None
        await self.playlists.update("p1", name="Renamed", public=False)
        call_args = self.http.put.call_args
        self.assertEqual(call_args.args[0], "/playlists/p1")
        self.assertEqual(
            call_args.kwargs["payload"],
            {"name": "Renamed", "public": False},
        )

    async def test_update_partial(self):
        self.http.put.return_value = None
        await self.playlists.update("p1", description="New desc")
        call_args = self.http.put.call_args
        self.assertEqual(call_args.kwargs["payload"], {"description": "New desc"})

    async def test_add(self):
        self.http.post.return_value = {"snapshot_id": "snap1"}
        result = await self.playlists.add("p1", ["spotify:track:a", "spotify:track:b"])
        self.assertEqual(result, "snap1")

    async def test_add_with_position(self):
        self.http.post.return_value = {"snapshot_id": "snap2"}
        await self.playlists.add("p1", ["spotify:track:a"], position=3)
        call_args = self.http.post.call_args
        self.assertEqual(call_args.kwargs["payload"]["position"], 3)

    async def test_remove(self):
        self.http.delete.return_value = {"snapshot_id": "snap3"}
        result = await self.playlists.remove("p1", ["spotify:track:a"])
        self.assertEqual(result, "snap3")
        call_args = self.http.delete.call_args
        self.assertEqual(
            call_args.kwargs["payload"],
            {"tracks": [{"uri": "spotify:track:a"}]},
        )

    async def test_reorder(self):
        self.http.put.return_value = {"snapshot_id": "snap4"}
        result = await self.playlists.reorder(
            "p1", range_start=0, insert_before=3, range_length=2
        )
        self.assertEqual(result, "snap4")

    async def test_cover_image(self):
        self.http.get.return_value = [
            {"url": "https://example.com/img.jpg", "height": 300, "width": 300}
        ]
        result = await self.playlists.cover_image("p1")
        self.assertEqual(len(result), 1)
        self.assertIsInstance(result[0], Image)

    async def test_cover_image_non_list_returns_empty(self):
        self.http.get.return_value = None
        result = await self.playlists.cover_image("p1")
        self.assertEqual(result, [])
