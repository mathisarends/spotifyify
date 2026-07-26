import json
import unittest
from types import SimpleNamespace
from unittest.mock import AsyncMock, call

try:
    import typer  # noqa: F401
except ModuleNotFoundError:
    raise unittest.SkipTest("typer is an optional CLI dependency") from None

from spotifyify.cli.player import _play_with_device_fallback, _select_fallback_device
from spotifyify.exceptions import SpotifyAPIError
from spotifyify.schemas import Device, PlaybackState
from tests.cli_harness import CliTestCase


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

    async def test_other_failures_are_not_mistaken_for_a_missing_device(self):
        error = SpotifyAPIError(403, "Premium required")
        player = SimpleNamespace(play=AsyncMock(side_effect=error), devices=AsyncMock())
        spotify = SimpleNamespace(player=player)

        with self.assertRaises(SpotifyAPIError) as raised:
            await _play_with_device_fallback(spotify, device_id=None)

        self.assertIs(raised.exception, error)
        player.devices.assert_not_awaited()


def _state(**overrides):
    payload = {"is_playing": True, "progress_ms": 0, "device": {"name": "Wohnzimmer"}}
    payload.update(overrides)
    return PlaybackState.model_validate(payload)


class PlayerCommandTestCase(CliTestCase):
    def player(self, states=None, **overrides):
        """A player namespace recording its calls, answering with `states`."""
        self.calls = []
        answers = list(states or [_state()])

        def recorder(name):
            async def command(*args, **kwargs):
                self.calls.append((name, args, kwargs))

            return command

        async def state(**kwargs):
            self.calls.append(("state", (), kwargs))
            return answers.pop(0) if len(answers) > 1 else answers[0]

        namespace = SimpleNamespace(
            play=recorder("play"),
            pause=recorder("pause"),
            skip=recorder("skip"),
            previous=recorder("previous"),
            seek=recorder("seek"),
            shuffle=recorder("shuffle"),
            repeat=recorder("repeat"),
            volume=recorder("volume"),
            add_to_queue=recorder("add_to_queue"),
            transfer=recorder("transfer"),
            state=state,
        )
        for name, value in overrides.items():
            setattr(namespace, name, value)
        return {"player": namespace}

    def call_names(self):
        return [name for name, _, _ in self.calls]


class TestPlaybackReporting(PlayerCommandTestCase):
    def test_nothing_playing_is_reported_as_stopped(self):
        async def state(**kwargs):
            return None

        rows = self.run_json(["player", "state"], self.player(state=state))

        self.assertEqual(
            rows, [{"state": "stopped", "track": "", "artists": [], "device": ""}]
        )

    def test_pause_waits_for_playback_to_actually_stop(self):
        states = [_state(), _state(is_playing=False)]

        rows = self.run_json(["player", "pause"], self.player(states))

        self.assertEqual(self.call_names().count("state"), 2)
        self.assertEqual(rows[0]["state"], "paused")

    def test_skip_waits_for_a_freshly_started_track(self):
        states = [_state(progress_ms=90_000), _state(progress_ms=100)]

        self.run_json(["player", "skip"], self.player(states))

        self.assertEqual(self.call_names(), ["skip", "state", "state"])

    def test_volume_and_seek_report_state_without_waiting_for_it(self):
        # There is nothing to wait for: neither changes what is playing.
        self.run_json(["player", "volume", "40"], self.player())
        self.assertEqual(self.call_names(), ["volume", "state"])

        self.run_json(["player", "seek", "1000"], self.player())
        self.assertEqual(self.call_names(), ["seek", "state"])

    def test_transfer_with_play_waits_for_playback_to_start(self):
        states = [_state(is_playing=False), _state()]

        rows = self.run_json(
            ["player", "transfer", "kitchen", "--play"], self.player(states)
        )

        self.assertEqual(self.call_names().count("state"), 2)
        self.assertEqual(rows[0]["state"], "playing")

    def test_transfer_without_play_has_nothing_to_wait_for(self):
        self.run_json(
            ["player", "transfer", "kitchen"], self.player([_state(is_playing=False)])
        )

        self.assertEqual(self.call_names(), ["transfer", "state"])


class TestPlayerArguments(PlayerCommandTestCase):
    def test_the_root_device_flag_targets_every_playback_command(self):
        self.run_json(["--device-id", "kitchen", "player", "pause"], self.player())

        self.assertEqual(self.calls[0][2]["device_id"], "kitchen")

    def test_the_device_environment_variable_does_the_same(self):
        self.run_json(
            ["player", "pause"], self.player(), env={"SPOTIFYIFY_DEVICE_ID": "kitchen"}
        )

        self.assertEqual(self.calls[0][2]["device_id"], "kitchen")

    def test_uris_can_be_repeated_or_comma_separated(self):
        self.run_json(
            ["player", "play", "--uri", "spotify:track:a,spotify:track:b"],
            self.player(),
        )

        self.assertEqual(
            self.calls[0][2]["uris"], ["spotify:track:a", "spotify:track:b"]
        )

    def test_a_json_offset_is_forwarded_as_an_object(self):
        self.run_json(
            [
                "player",
                "play",
                "--context-uri",
                "spotify:album:a1",
                "--offset-json",
                '{"position": 3}',
            ],
            self.player(),
        )

        self.assertEqual(self.calls[0][2]["offset"], {"position": 3})

    def test_a_malformed_offset_is_rejected_before_anything_plays(self):
        result = self.run_cli(
            ["player", "play", "--offset-json", "{position: 3}"], self.player()
        )

        self.assertNotEqual(result.exit_code, 0)
        self.assertEqual(self.calls, [])

    def test_a_negative_position_is_rejected(self):
        result = self.run_cli(["player", "seek", "--", "-1"], self.player())

        self.assertNotEqual(result.exit_code, 0)
        self.assertEqual(self.calls, [])

    def test_a_volume_above_one_hundred_is_rejected(self):
        result = self.run_cli(["player", "volume", "101"], self.player())

        self.assertNotEqual(result.exit_code, 0)
        self.assertEqual(self.calls, [])


class TestQueueing(PlayerCommandTestCase):
    def test_every_uri_is_queued_in_the_order_it_was_given(self):
        self.run_json(
            [
                "player",
                "add-to-queue",
                "spotify:track:a,spotify:track:b",
                "spotify:track:c",
            ],
            self.player(),
        )

        queued = [args[0] for name, args, _ in self.calls if name == "add_to_queue"]
        self.assertEqual(
            queued, ["spotify:track:a", "spotify:track:b", "spotify:track:c"]
        )

    def test_the_queue_is_listed_with_its_declared_columns(self):
        async def queue():
            return {
                "queue": [
                    {
                        "id": "t1",
                        "name": "HAMPELMANN",
                        "artists": [{"name": "Ikkimel"}],
                        "uri": "spotify:track:t1",
                        "available_markets": ["DE"],
                    }
                ]
            }

        rows = self.run_json(["player", "queue"], self.player(queue=queue))

        self.assertEqual(list(rows[0]), ["id", "name", "artists", "uri"])
        self.assertEqual(rows[0]["artists"], ["Ikkimel"])


class TestDeviceListing(PlayerCommandTestCase):
    DEVICES = [
        Device(id="z", name="Workstation", type="Computer"),
        Device(id="a", name="Desktop", type="Computer"),
    ]

    def devices(self):
        async def devices():
            return list(self.DEVICES)

        return self.player(devices=devices)

    def test_devices_are_ordered_reproducibly(self):
        # Spotify returns devices in no defined order, so repeated calls (and
        # anything cached on top of them) would otherwise differ run to run.
        rows = self.run_json(["player", "devices"], self.devices())

        self.assertEqual([row["id"] for row in rows], ["a", "z"])

    def test_raw_output_keeps_the_order_spotify_sent(self):
        result = self.run_cli(
            ["player", "devices"], self.devices(), env={"SPOTIFYIFY_RAW": "1"}
        )

        self.assertEqual(result.exit_code, 0, result.output)
        self.assertEqual(
            [device["id"] for device in json.loads(result.output)], ["z", "a"]
        )

    def test_no_devices_is_an_empty_list_not_an_error(self):
        async def devices():
            return []

        rows = self.run_json(["player", "devices"], self.player(devices=devices))

        self.assertEqual(rows, [])
