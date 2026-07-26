import asyncio
import os
import unittest
from types import SimpleNamespace
from unittest.mock import patch

from spotifyify import SpotifyScope
from spotifyify.cli import core
from spotifyify.schemas import PlaybackState
from tests.conftest import episode, simplified_show


class TestParseJsonObject(unittest.TestCase):
    def setUp(self):
        if core.typer is None:
            self.skipTest("typer is optional")

    def test_no_value_means_no_object(self):
        self.assertIsNone(core.parse_json_object(None, "--offset-json"))
        self.assertIsNone(core.parse_json_object("", "--offset-json"))

    def test_an_object_is_returned_as_a_dict(self):
        self.assertEqual(
            core.parse_json_object('{"position": 3}', "--offset-json"),
            {"position": 3},
        )

    def test_malformed_json_names_the_option_it_came_from(self):
        with self.assertRaises(core.typer.BadParameter) as raised:
            core.parse_json_object("{position: 3}", "--offset-json")

        self.assertIn("--offset-json", str(raised.exception))

    def test_json_that_is_not_an_object_is_rejected(self):
        # A bare array parses fine but would build a request body Spotify rejects.
        with self.assertRaises(core.typer.BadParameter):
            core.parse_json_object("[1, 2]", "--offset-json")

    def test_without_typer_the_same_input_raises_a_plain_value_error(self):
        with patch.object(core, "typer", None):
            with self.assertRaises(ValueError):
                core.parse_json_object("[1, 2]", "--offset-json")
            with self.assertRaises(ValueError):
                core.parse_json_object("{position: 3}", "--offset-json")


class TestMergeScopes(unittest.TestCase):
    def test_duplicates_collapse_and_first_mention_fixes_the_order(self):
        merged = core.merge_scopes(
            [SpotifyScope.USER_MODIFY_PLAYBACK_STATE],
            [
                SpotifyScope.USER_READ_PLAYBACK_STATE,
                SpotifyScope.USER_MODIFY_PLAYBACK_STATE,
            ],
        )

        self.assertEqual(
            merged,
            [
                SpotifyScope.USER_MODIFY_PLAYBACK_STATE,
                SpotifyScope.USER_READ_PLAYBACK_STATE,
            ],
        )

    def test_no_groups_means_no_scopes(self):
        self.assertEqual(core.merge_scopes(), [])


class TestDefaults(unittest.TestCase):
    """--market/--device-id from the root command, then the environment."""

    def setUp(self):
        core.set_default_market(None)
        core.set_default_device_id(None)
        self.addCleanup(core.set_default_market, None)
        self.addCleanup(core.set_default_device_id, None)

    def test_market_falls_back_to_the_environment(self):
        with patch.dict(os.environ, {core.MARKET_ENV_VAR: "DE"}):
            self.assertEqual(core.default_market(), "DE")

    def test_the_root_flag_wins_over_the_environment(self):
        core.set_default_market("US")

        with patch.dict(os.environ, {core.MARKET_ENV_VAR: "DE"}):
            self.assertEqual(core.default_market(), "US")

    def test_an_empty_environment_value_counts_as_unset(self):
        with patch.dict(os.environ, {core.MARKET_ENV_VAR: ""}):
            self.assertIsNone(core.default_market())

    def test_device_id_follows_the_same_precedence(self):
        with patch.dict(os.environ, {core.DEVICE_ENV_VAR: "from-env"}):
            self.assertEqual(core.default_device_id(), "from-env")
            core.set_default_device_id("from-flag")
            self.assertEqual(core.default_device_id(), "from-flag")

    def test_nothing_configured_means_no_default(self):
        with patch.dict(os.environ, {}, clear=True):
            self.assertIsNone(core.default_market())
            self.assertIsNone(core.default_device_id())

    def test_raw_output_is_opt_in(self):
        with patch.dict(os.environ, {}, clear=True):
            self.assertFalse(core.is_raw_output())
        with patch.dict(os.environ, {core.RAW_ENV_VAR: "0"}):
            self.assertFalse(core.is_raw_output())
        with patch.dict(os.environ, {core.RAW_ENV_VAR: "1"}):
            self.assertTrue(core.is_raw_output())


class TestProjection(unittest.TestCase):
    def test_a_queue_envelope_is_unwrapped_like_a_paging_one(self):
        payload = {"queue": [{"id": "t1", "name": "Track"}]}

        self.assertEqual(
            core.rows(payload, ("id", "name")), [{"id": "t1", "name": "Track"}]
        )

    def test_a_single_object_becomes_one_row(self):
        self.assertEqual(core.rows({"id": "t1"}, ("id",)), [{"id": "t1"}])

    def test_no_payload_means_no_rows(self):
        self.assertEqual(core.rows(None, ("id",)), [])

    def test_missing_paths_are_reported_as_null_rather_than_dropped(self):
        # Every row keeps the same keys, so callers can index the output blindly.
        rows = core.rows([{"id": "t1"}], ("id", "album.name"))

        self.assertEqual(rows, [{"id": "t1", "album.name": None}])

    def test_an_object_without_a_name_or_id_keeps_its_fields(self):
        rows = core.rows(
            [{"external_urls": {"spotify": "https://x"}}], ("external_urls",)
        )

        self.assertEqual(rows[0]["external_urls"], {"spotify": "https://x"})

    def test_filter_fields_without_fields_passes_the_value_through(self):
        payload = [{"id": "t1", "name": "Track"}]

        self.assertIs(core.filter_fields(payload, []), payload)

    def test_get_path_walks_into_pydantic_models(self):
        state = PlaybackState.model_validate(
            {"is_playing": True, "device": {"name": "Wohnzimmer"}}
        )

        self.assertEqual(core.get_path(state, "device.name"), "Wohnzimmer")

    def test_get_path_stops_at_an_out_of_range_index(self):
        self.assertIsNone(core.get_path({"items": []}, "items.0.name"))

    def test_cells_render_booleans_and_lists_readably(self):
        self.assertEqual(core.cell(True), "true")
        self.assertEqual(core.cell(False), "false")
        self.assertEqual(core.cell(None), "")
        self.assertEqual(core.cell([{"name": "A"}, {"name": "B"}]), "A, B")


class TestSorting(unittest.TestCase):
    def test_a_queue_envelope_is_sorted_in_place_of_items(self):
        payload = {"queue": [{"n": 2}, {"n": 1}]}

        self.assertEqual(core.apply_sort(payload, ["n"])["queue"], [{"n": 1}, {"n": 2}])

    def test_later_keys_break_ties_left_by_earlier_ones(self):
        items = [
            {"artist": "B", "name": "1"},
            {"artist": "A", "name": "2"},
            {"artist": "A", "name": "1"},
        ]

        ordered = core.sort_items(items, ["artist", "name"])

        self.assertEqual(
            [(item["artist"], item["name"]) for item in ordered],
            [("A", "1"), ("A", "2"), ("B", "1")],
        )

    def test_mixed_types_sort_without_raising(self):
        items = [{"n": "text"}, {"n": 2}, {"n": None}, {"n": True}]

        ordered = core.sort_items(items, ["n"])

        # Numbers (and booleans) first, then text, then absent values.
        self.assertEqual([item["n"] for item in ordered], [True, 2, "text", None])

    def test_text_sorts_case_insensitively(self):
        items = [{"n": "beta"}, {"n": "Alpha"}]

        self.assertEqual(
            [item["n"] for item in core.sort_items(items, ["n"])], ["Alpha", "beta"]
        )

    def test_an_empty_sort_spec_is_ignored(self):
        payload = {"items": [{"n": 2}, {"n": 1}]}

        self.assertIs(core.apply_sort(payload, []), payload)


class TestBatching(unittest.IsolatedAsyncioTestCase):
    async def test_reads_are_chunked_and_concatenated_in_request_order(self):
        chunks = []

        async def action(chunk):
            chunks.append(list(chunk))
            return [f"item:{value}" for value in chunk]

        result = await core.gather_batches(action, list("abcde"), 2)

        self.assertEqual(chunks, [["a", "b"], ["c", "d"], ["e"]])
        self.assertEqual(result, [f"item:{value}" for value in "abcde"])

    async def test_read_batches_run_concurrently(self):
        in_flight = 0
        peak = 0

        async def action(chunk):
            nonlocal in_flight, peak
            in_flight += 1
            peak = max(peak, in_flight)
            await asyncio.sleep(0)
            in_flight -= 1
            return chunk

        await core.gather_batches(action, list("abcd"), 1)

        self.assertEqual(peak, 4)

    async def test_no_ids_means_no_request(self):
        calls = []

        async def action(chunk):
            calls.append(chunk)
            return chunk

        self.assertEqual(await core.gather_batches(action, [], 10), [])
        await core.sequential_batches(action, [], 10)

        self.assertEqual(calls, [])

    async def test_writes_finish_one_chunk_before_starting_the_next(self):
        # Partial failures have to stay comprehensible, so writes never overlap.
        events = []

        async def action(chunk):
            events.append(("start", tuple(chunk)))
            await asyncio.sleep(0)
            events.append(("done", tuple(chunk)))

        await core.sequential_batches(action, list("abc"), 2)

        self.assertEqual(
            events,
            [
                ("start", ("a", "b")),
                ("done", ("a", "b")),
                ("start", ("c",)),
                ("done", ("c",)),
            ],
        )


def _state(**overrides):
    payload = {"is_playing": True, "progress_ms": 0}
    payload.update(overrides)
    return PlaybackState.model_validate(payload)


class TestPlaybackPredicates(unittest.TestCase):
    def test_nothing_playing_satisfies_no_predicate(self):
        self.assertFalse(core.is_playing(None))
        self.assertFalse(core.is_paused(None))
        self.assertFalse(core.is_fresh_track(None))

    def test_a_track_already_in_progress_is_not_fresh(self):
        self.assertFalse(core.is_fresh_track(_state(progress_ms=60_000)))
        self.assertTrue(core.is_fresh_track(_state(progress_ms=1_000)))

    def test_plays_uri_rejects_the_track_that_was_already_playing(self):
        matches = core.plays_uri("spotify:track:new")
        previous = _state(item={"type": "track", "uri": "spotify:track:old"})

        self.assertFalse(matches(previous))
        self.assertTrue(
            matches(_state(item={"type": "track", "uri": "spotify:track:new"}))
        )

    def test_without_a_uri_any_freshly_started_track_counts(self):
        self.assertIs(core.plays_uri(None), core.is_fresh_track)


class TestSettledPlayback(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        patcher = patch.object(core, "SETTLE_DELAY_SECONDS", 0)
        patcher.start()
        self.addCleanup(patcher.stop)

    def _spotify(self, states):
        reads = []

        async def state():
            reads.append(1)
            return states[min(len(reads) - 1, len(states) - 1)]

        return SimpleNamespace(player=SimpleNamespace(state=state)), reads

    async def test_polling_stops_as_soon_as_the_predicate_holds(self):
        spotify, reads = self._spotify([_state(is_playing=False), _state()])

        result = await core.settled_playback(spotify, until=core.is_playing)

        self.assertEqual(len(reads), 2)
        self.assertTrue(result.is_playing)

    async def test_polling_gives_up_and_reports_what_it_last_saw(self):
        spotify, reads = self._spotify([_state(is_playing=False)])

        result = await core.settled_playback(spotify, until=core.is_playing)

        self.assertEqual(len(reads), core.SETTLE_ATTEMPTS)
        self.assertFalse(result.is_playing)

    async def test_no_wait_reads_once_even_with_a_predicate(self):
        spotify, reads = self._spotify([_state(is_playing=False)])

        await core.settled_playback(spotify, until=core.is_playing, wait=False)

        self.assertEqual(len(reads), 1)

    async def test_without_a_predicate_there_is_nothing_to_wait_for(self):
        spotify, reads = self._spotify([_state(is_playing=False)])

        await core.settled_playback(spotify)

        self.assertEqual(len(reads), 1)


class TestPlaybackSummary(unittest.TestCase):
    def test_an_episode_reports_its_publisher_and_show(self):
        state = PlaybackState.model_validate(
            {
                "is_playing": True,
                "item": episode(
                    type="episode",
                    name="Folge 1",
                    show=simplified_show(name="Der Podcast", publisher="ARD"),
                ),
            }
        )

        summary = core.playback_summary(state)

        # Episodes have no artists, so the publisher fills the same column.
        self.assertEqual(summary["artists"], ["ARD"])
        self.assertEqual(summary["album"], "Der Podcast")
        self.assertEqual(summary["track"], "Folge 1")

    def test_every_summary_has_the_same_keys(self):
        state = PlaybackState.model_validate(
            {"is_playing": True, "item": {"type": "track", "name": "Track"}}
        )

        self.assertEqual(
            core.playback_summary(state).keys(), core.playback_summary(None).keys()
        )

    def test_progress_shuffle_and_repeat_reach_the_summary(self):
        state = PlaybackState.model_validate(
            {
                "is_playing": True,
                "progress_ms": 4200,
                "shuffle_state": True,
                "repeat_state": "context",
                "item": {"type": "track", "name": "Track", "duration_ms": 180_000},
            }
        )

        summary = core.playback_summary(state)

        self.assertEqual(summary["progress_ms"], 4200)
        self.assertEqual(summary["duration_ms"], 180_000)
        self.assertTrue(summary["shuffle"])
        self.assertEqual(summary["repeat"], "context")


if __name__ == "__main__":
    unittest.main()
