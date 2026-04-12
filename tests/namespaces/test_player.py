import unittest
from unittest.mock import AsyncMock

from tests.conftest import cursor_paging
from spotifyify.namespaces.player import Player
from spotifyify.schemas import (
    CursorPagingPlayHistory,
    Device,
    PlaybackState,
    PlayerQueue,
)


class TestPlayer(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        self.http = AsyncMock()
        self.player = Player(self.http)

    async def test_state(self):
        self.http.get.return_value = {
            "is_playing": True,
            "device": {
                "id": "d1",
                "name": "Phone",
                "type": "Smartphone",
                "volume_percent": 50,
            },
        }
        result = await self.player.state()
        self.assertIsInstance(result, PlaybackState)

    async def test_state_returns_none_when_inactive(self):
        self.http.get.return_value = None
        result = await self.player.state()
        self.assertIsNone(result)

    async def test_play(self):
        self.http.put.return_value = None
        await self.player.play(context_uri="spotify:album:abc", device_id="d1")
        self.http.put.assert_called_once_with(
            "/me/player/play",
            params={"device_id": "d1"},
            payload={"context_uri": "spotify:album:abc"},
        )

    async def test_play_with_uris(self):
        self.http.put.return_value = None
        await self.player.play(uris=["spotify:track:a", "spotify:track:b"])
        call_kwargs = self.http.put.call_args
        self.assertEqual(
            call_kwargs.kwargs["payload"]["uris"],
            ["spotify:track:a", "spotify:track:b"],
        )

    async def test_pause(self):
        self.http.put.return_value = None
        await self.player.pause()
        self.http.put.assert_called_once_with("/me/player/pause", params=None)

    async def test_skip(self):
        self.http.post.return_value = None
        await self.player.skip()
        self.http.post.assert_called_once_with("/me/player/next", params=None)

    async def test_previous(self):
        self.http.post.return_value = None
        await self.player.previous()
        self.http.post.assert_called_once_with("/me/player/previous", params=None)

    async def test_seek(self):
        self.http.put.return_value = None
        await self.player.seek(30000)
        self.http.put.assert_called_once_with(
            "/me/player/seek", params={"position_ms": 30000}
        )

    async def test_repeat(self):
        self.http.put.return_value = None
        await self.player.repeat("track")
        self.http.put.assert_called_once_with(
            "/me/player/repeat", params={"state": "track"}
        )

    async def test_shuffle(self):
        self.http.put.return_value = None
        await self.player.shuffle(True)
        self.http.put.assert_called_once_with(
            "/me/player/shuffle", params={"state": True}
        )

    async def test_volume(self):
        self.http.put.return_value = None
        await self.player.volume(75)
        self.http.put.assert_called_once_with(
            "/me/player/volume", params={"volume_percent": 75}
        )

    async def test_queue(self):
        self.http.get.return_value = {"currently_playing": None, "queue": []}
        result = await self.player.queue()
        self.assertIsInstance(result, PlayerQueue)

    async def test_add_to_queue(self):
        self.http.post.return_value = None
        await self.player.add_to_queue("spotify:track:abc")
        self.http.post.assert_called_once_with(
            "/me/player/queue", params={"uri": "spotify:track:abc"}
        )

    async def test_transfer(self):
        self.http.put.return_value = None
        await self.player.transfer("d1", play=True)
        self.http.put.assert_called_once_with(
            "/me/player",
            payload={"device_ids": ["d1"], "play": True},
        )

    async def test_devices(self):
        self.http.get.return_value = {
            "devices": [
                {
                    "id": "d1",
                    "name": "Phone",
                    "type": "Smartphone",
                    "volume_percent": 50,
                }
            ]
        }
        result = await self.player.devices()
        self.assertEqual(len(result), 1)
        self.assertIsInstance(result[0], Device)

    async def test_recently_played(self):
        self.http.get.return_value = cursor_paging()
        result = await self.player.recently_played(limit=5)
        self.assertIsInstance(result, CursorPagingPlayHistory)
