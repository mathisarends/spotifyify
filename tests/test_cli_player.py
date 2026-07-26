import unittest
from types import SimpleNamespace
from unittest.mock import AsyncMock, call

try:
    import typer  # noqa: F401
except ModuleNotFoundError:
    raise unittest.SkipTest("typer is an optional CLI dependency") from None

from spotifyify.cli.player import _play_with_device_fallback, _select_fallback_device
from spotifyify.exceptions import SpotifyAPIError
from spotifyify.schemas import Device


class TestDeviceFallback(unittest.IsolatedAsyncioTestCase):
    def test_selects_active_then_computer_then_name(self):
        devices = [
            Device(id="tv", name="Living Room", type="TV"),
            Device(id="z", name="Workstation", type="Computer"),
            Device(id="a", name="Desktop", type="Computer"),
            Device(
                id="restricted",
                name="Restricted",
                type="Computer",
                is_restricted=True,
            ),
        ]

        self.assertEqual(_select_fallback_device(devices).id, "a")

        devices[0].is_active = True
        self.assertEqual(_select_fallback_device(devices).id, "tv")

    def test_returns_none_without_a_controllable_device(self):
        devices = [
            Device(id=None, name="Missing ID"),
            Device(id="restricted", is_restricted=True),
        ]

        self.assertIsNone(_select_fallback_device(devices))

    async def test_discovers_and_retries_on_no_active_device(self):
        player = SimpleNamespace(
            play=AsyncMock(
                side_effect=[
                    SpotifyAPIError(
                        404, "Player command failed: No active device found"
                    ),
                    None,
                ]
            ),
            devices=AsyncMock(
                return_value=[
                    Device(id="tv", name="Living Room", type="TV"),
                    Device(id="computer", name="Desktop", type="Computer"),
                ]
            ),
        )
        spotify = SimpleNamespace(player=player)

        await _play_with_device_fallback(
            spotify,
            device_id=None,
            uris=["spotify:track:123"],
        )

        player.devices.assert_awaited_once_with()
        self.assertEqual(
            player.play.await_args_list,
            [
                call(
                    device_id=None,
                    context_uri=None,
                    uris=["spotify:track:123"],
                    offset=None,
                    position_ms=None,
                ),
                call(
                    device_id="computer",
                    context_uri=None,
                    uris=["spotify:track:123"],
                    offset=None,
                    position_ms=None,
                ),
            ],
        )

    async def test_does_not_override_an_explicit_device(self):
        error = SpotifyAPIError(404, "No active device found")
        player = SimpleNamespace(
            play=AsyncMock(side_effect=error),
            devices=AsyncMock(),
        )
        spotify = SimpleNamespace(player=player)

        with self.assertRaises(SpotifyAPIError) as raised:
            await _play_with_device_fallback(spotify, device_id="chosen")

        self.assertIs(raised.exception, error)
        player.devices.assert_not_awaited()

    async def test_reraises_when_discovery_has_no_controllable_device(self):
        error = SpotifyAPIError(404, "No active device found")
        player = SimpleNamespace(
            play=AsyncMock(side_effect=error),
            devices=AsyncMock(
                return_value=[Device(id="restricted", is_restricted=True)]
            ),
        )
        spotify = SimpleNamespace(player=player)

        with self.assertRaises(SpotifyAPIError) as raised:
            await _play_with_device_fallback(spotify, device_id=None)

        self.assertIs(raised.exception, error)
        self.assertEqual(player.play.await_count, 1)
