import unittest
from unittest.mock import AsyncMock

from tests.conftest import cursor_paging
from spotifyify.namespaces.users import Users
from spotifyify.schemas import CursorPagingSimplifiedArtist, PublicUser, User


class TestUsers(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        self.http = AsyncMock()
        self.users = Users(self.http)

    async def test_me(self):
        self.http.get.return_value = {"id": "user1", "display_name": "Test User"}
        result = await self.users.me()
        self.assertIsInstance(result, User)
        self.http.get.assert_called_once_with("/me")

    async def test_get(self):
        self.http.get.return_value = {"id": "user2", "display_name": "Other"}
        result = await self.users.get("user2")
        self.assertIsInstance(result, PublicUser)
        self.http.get.assert_called_once_with("/users/user2", require_user=False)

    async def test_following(self):
        self.http.get.return_value = {"artists": cursor_paging()}
        result = await self.users.following(limit=10)
        self.assertIsInstance(result, CursorPagingSimplifiedArtist)

    async def test_follow(self):
        self.http.put.return_value = None
        await self.users.follow("artist", ["id1", "id2"])
        self.http.put.assert_called_once_with(
            "/me/following",
            params={"type": "artist"},
            payload={"ids": ["id1", "id2"]},
        )

    async def test_unfollow(self):
        self.http.delete.return_value = None
        await self.users.unfollow("artist", ["id1"])
        self.http.delete.assert_called_once_with(
            "/me/following",
            params={"type": "artist"},
            payload={"ids": ["id1"]},
        )

    async def test_check_following(self):
        self.http.get.return_value = [True, False]
        result = await self.users.check_following("artist", ["id1", "id2"])
        self.assertEqual(result, [True, False])

    async def test_check_following_non_list(self):
        self.http.get.return_value = None
        result = await self.users.check_following("artist", ["id1"])
        self.assertEqual(result, [])
