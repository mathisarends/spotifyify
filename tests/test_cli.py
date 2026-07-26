import json
import pathlib
import tomllib
import unittest
from types import SimpleNamespace
from unittest.mock import patch

from spotifyify import SpotifyScope, cli
from spotifyify.schemas import PlaybackState


class TestCli(unittest.TestCase):
    def test_package_metadata_exposes_optional_cli(self):
        pyproject_path = pathlib.Path(__file__).parents[1] / "pyproject.toml"
        pyproject = tomllib.loads(pyproject_path.read_text(encoding="utf-8"))

        self.assertEqual(
            pyproject["project"]["scripts"]["spotifyify"],
            "spotifyify.cli:main",
        )
        self.assertIn(
            "typer>=0.16.0", pyproject["project"]["optional-dependencies"]["cli"]
        )

    def test_main_explains_missing_optional_dependency(self):
        with patch.object(cli, "typer", None):
            with self.assertRaises(SystemExit) as raised:
                cli.main()

        self.assertEqual(str(raised.exception), cli.INSTALL_MESSAGE)

    def test_parse_scopes_accepts_repeated_and_csv_values(self):
        result = cli._parse_scopes(
            [
                "user-read-playback-state,playlist-read-private",
                "custom-scope",
            ]
        )

        self.assertEqual(
            result,
            [
                SpotifyScope.USER_READ_PLAYBACK_STATE,
                SpotifyScope.PLAYLIST_READ_PRIVATE,
                "custom-scope",
            ],
        )

    def test_split_values_accepts_repeated_and_csv_values(self):
        self.assertEqual(
            cli._split_values(["a,b", "c d"]),
            ["a", "b", "c", "d"],
        )

    def test_filter_fields_supports_nested_paths_and_lists(self):
        payload = {
            "items": [
                {
                    "id": "track_id",
                    "name": "Track",
                    "album": {"name": "Album"},
                }
            ],
            "total": 1,
        }

        self.assertEqual(
            cli._filter_fields(payload["items"], ["id", "album.name"]),
            [{"id": "track_id", "album.name": "Album"}],
        )
        self.assertEqual(cli._get_path(payload, "items.0.name"), "Track")

    def test_table_formats_headers_and_rows(self):
        table = cli._table(("ID", "Name"), [["1", "Track"], ["22", "Other"]])

        self.assertEqual(
            table,
            "ID  Name \n--  -----\n1   Track\n22  Other",
        )

    def test_table_handles_empty_results(self):
        self.assertEqual(cli._table(("ID",), []), "No results.")

    def test_typer_app_registers_all_namespace_groups_when_available(self):
        if cli.typer is None:
            self.skipTest("typer is optional")

        registered_names = {
            group.name for group in cli.app.registered_groups if group.name
        }

        self.assertEqual(
            registered_names,
            {
                "tracks",
                "artists",
                "albums",
                "playlists",
                "shows",
                "episodes",
                "library",
                "player",
                "users",
            },
        )


class TestOutputContract(unittest.TestCase):
    """The format a command emits depends only on arguments and environment."""

    def test_json_is_the_default_format(self):
        with patch.dict("os.environ", {}, clear=True):
            self.assertEqual(cli._resolve_format(None), "json")

    def test_explicit_format_wins_over_everything(self):
        with patch.dict("os.environ", {"SPOTIFYIFY_FORMAT": "json"}, clear=True):
            self.assertEqual(
                cli._resolve_format("table", json_output=True),
                "table",
            )

    def test_environment_overrides_the_default(self):
        with patch.dict("os.environ", {"SPOTIFYIFY_FORMAT": "table"}, clear=True):
            self.assertEqual(cli._resolve_format(None), "table")

    def test_json_flag_is_shorthand_for_json_format(self):
        with patch.dict("os.environ", {"SPOTIFYIFY_FORMAT": "table"}, clear=True):
            self.assertEqual(cli._resolve_format(None, json_output=True), "json")

    def test_unknown_format_is_rejected(self):
        with self.assertRaises(Exception) as raised:
            cli._resolve_format("yaml")

        self.assertIn("--format", str(raised.exception))

    def test_rows_keep_declared_column_order_and_flatten_nested_objects(self):
        payload = {
            "items": [
                {
                    "id": "t1",
                    "name": "Track",
                    "artists": [{"name": "A"}, {"name": "B"}],
                    "album": {"name": "Album"},
                    "duration_ms": 1000,
                }
            ]
        }

        rows = cli._rows(
            payload, ("id", "name", "artists", "album.name", "duration_ms")
        )

        self.assertEqual(
            list(rows[0]),
            ["id", "name", "artists", "album.name", "duration_ms"],
        )
        self.assertEqual(rows[0]["artists"], ["A", "B"])
        self.assertEqual(rows[0]["album.name"], "Album")
        # Numbers stay numbers rather than being stringified.
        self.assertEqual(rows[0]["duration_ms"], 1000)

    def test_cells_never_contain_control_characters(self):
        rows = cli._rows([{"name": "a\tb\nc\x1b[31m"}], ("name",))

        self.assertNotIn("\t", cli._cell(rows[0]["name"]))
        self.assertNotIn("\n", cli._cell(rows[0]["name"]))
        self.assertNotIn("\x1b", cli._cell(rows[0]["name"]))


class TestStableOrdering(unittest.TestCase):
    def test_sort_is_stable_so_ties_keep_api_order(self):
        items = [
            {"name": "same", "id": "first"},
            {"name": "same", "id": "second"},
            {"name": "same", "id": "third"},
        ]

        ordered = cli._sort_items(items, ["name"])

        self.assertEqual([item["id"] for item in ordered], ["first", "second", "third"])

    def test_sort_handles_missing_values_without_raising(self):
        items = [{"n": 2}, {"n": None}, {"n": 1}, {}]

        ordered = cli._sort_items(items, ["n"])

        # Numbers first in order, absent values last.
        self.assertEqual([item.get("n") for item in ordered], [1, 2, None, None])

    def test_descending_sort_uses_a_leading_dash(self):
        items = [{"n": 1}, {"n": 3}, {"n": 2}]

        ordered = cli._sort_items(items, ["-n"])

        self.assertEqual([item["n"] for item in ordered], [3, 2, 1])

    def test_sort_applies_inside_a_paging_envelope(self):
        payload = {"total": 2, "items": [{"n": 2}, {"n": 1}]}

        result = cli._apply_sort(payload, ["n"])

        self.assertEqual(result["items"], [{"n": 1}, {"n": 2}])
        self.assertEqual(result["total"], 2)


class TestWhereFilter(unittest.TestCase):
    def test_where_keeps_matching_rows_case_insensitively(self):
        payload = {"items": [{"name": "Alpha"}, {"name": "Beta"}]}

        result = cli._apply_where(payload, ["name=alp"])

        self.assertEqual(result["items"], [{"name": "Alpha"}])

    def test_where_predicates_are_combined_with_and(self):
        payload = {"items": [{"a": "x", "b": "y"}, {"a": "x", "b": "z"}]}

        result = cli._apply_where(payload, ["a=x", "b=z"])

        self.assertEqual(result["items"], [{"a": "x", "b": "z"}])

    def test_where_rejects_a_missing_separator(self):
        with self.assertRaises(Exception) as raised:
            cli._apply_where([{"a": 1}], ["nope"])

        self.assertIn("PATH=VALUE", str(raised.exception))


class TestPlaybackSummary(unittest.TestCase):
    def test_summary_of_no_playback_is_stopped(self):
        summary = cli._playback_summary(None)

        self.assertEqual(summary["state"], "stopped")
        self.assertEqual(summary["artists"], [])

    def test_summary_reports_state_track_artists_and_device(self):
        state = PlaybackState.model_validate(
            {
                "is_playing": True,
                "device": {"name": "Wohnzimmer"},
                "item": {
                    "type": "track",
                    "name": "HAMPELMANN",
                    "artists": [{"name": "Ikkimel"}],
                },
            }
        )

        summary = cli._playback_summary(state)

        self.assertEqual(summary["state"], "playing")
        self.assertEqual(summary["track"], "HAMPELMANN")
        self.assertEqual(summary["artists"], ["Ikkimel"])
        self.assertEqual(summary["device"], "Wohnzimmer")

    def test_paused_playback_is_reported_as_paused(self):
        state = PlaybackState.model_validate({"is_playing": False})

        self.assertEqual(cli._playback_summary(state)["state"], "paused")


class TestBatching(unittest.TestCase):
    def test_ids_are_chunked_to_the_endpoint_limit(self):
        from spotifyify.cli._core import _chunked

        self.assertEqual(_chunked(["a", "b", "c"], 2), [["a", "b"], ["c"]])
        self.assertEqual(_chunked([], 2), [])


class TestAliasTolerance(unittest.TestCase):
    def setUp(self):
        if cli.typer is None:
            self.skipTest("typer is optional")
        import click

        self.root = cli.typer.main.get_command(cli.app)
        self.ctx = click.Context(self.root)

    def _resolves(self, name):
        return self.root.get_command(self.ctx, name)

    def test_singular_group_names_resolve_to_the_plural_group(self):
        self.assertIsNotNone(self._resolves("artist"))
        self.assertIsNotNone(self._resolves("track"))

    def test_canonical_names_still_resolve(self):
        self.assertIsNotNone(self._resolves("artists"))

    def test_unknown_names_still_fail(self):
        self.assertIsNone(self._resolves("definitely-not-a-command"))

    def test_get_many_is_accepted_as_get(self):
        import click

        artists = self._resolves("artists")
        command = artists.get_command(click.Context(artists), "get-many")

        self.assertIsNotNone(command)
        self.assertEqual(command.name, "get")


class TestAgentHelp(unittest.TestCase):
    def setUp(self):
        if cli.typer is None:
            self.skipTest("typer is optional")
        self.text = cli.agent_help(cli.typer.main.get_command(cli.app))

    def test_every_group_appears(self):
        for group in ("tracks", "artists", "albums", "playlists", "player", "library"):
            self.assertIn(f"{group}: ", self.text)

    def test_the_output_contract_is_stated(self):
        self.assertIn("JSON on stdout", self.text)
        self.assertIn("--sort", self.text)
        self.assertIn("Mutations print the state they produced", self.text)

    def test_variadic_arguments_are_marked(self):
        self.assertIn("get TRACK_IDS...", self.text)

    def test_it_stays_small_enough_for_a_system_prompt(self):
        self.assertLess(len(self.text), 4000)


class FakeSpotifyify:
    """Stands in for the real client inside the CLI's async runner."""

    namespaces: dict = {}

    def __init__(self, **kwargs):
        self.scopes = kwargs.get("scopes")
        for name, value in self.namespaces.items():
            setattr(self, name, value)

    async def __aenter__(self):
        return self

    async def __aexit__(self, *exc_info):
        return False


class TestEndToEnd(unittest.TestCase):
    def setUp(self):
        if cli.typer is None:
            self.skipTest("typer is optional")
        from typer.testing import CliRunner

        self.runner = CliRunner()

    def _run(self, args, namespaces):
        FakeSpotifyify.namespaces = namespaces
        with patch("spotifyify.cli._core.Spotifyify", FakeSpotifyify):
            return self.runner.invoke(cli.app, args)

    def test_search_prints_declared_columns_as_json_by_default(self):
        async def find(query, **kwargs):
            return {
                "items": [
                    {
                        "id": "t1",
                        "name": "WHO'S THAT",
                        "artists": [{"name": "Ikkimel"}],
                        "album": {"name": "WHO'S THAT"},
                        "uri": "spotify:track:t1",
                        "available_markets": ["DE"] * 100,
                    }
                ]
            }

        result = self._run(
            ["tracks", "search", "Ikkimel"],
            {"tracks": SimpleNamespace(find=find)},
        )

        self.assertEqual(result.exit_code, 0, result.output)
        rows = json.loads(result.output)
        self.assertEqual(list(rows[0]), ["id", "name", "artists", "album.name", "uri"])
        # The noisy payload fields never reach the caller.
        self.assertNotIn("available_markets", result.output)

    def test_raw_returns_the_untouched_payload(self):
        async def find(query, **kwargs):
            return {"items": [{"id": "t1", "available_markets": ["DE"]}], "total": 1}

        result = self._run(
            ["tracks", "search", "x", "--raw"],
            {"tracks": SimpleNamespace(find=find)},
        )

        self.assertEqual(result.exit_code, 0, result.output)
        self.assertIn("available_markets", result.output)
        self.assertEqual(json.loads(result.output)["total"], 1)

    def test_player_state_raw_returns_the_unprojected_playback_payload(self):
        async def state(**kwargs):
            return PlaybackState.model_validate(
                {
                    "is_playing": True,
                    "device": {"name": "Wohnzimmer"},
                    "item": {
                        "type": "track",
                        "name": "HAMPELMANN",
                        "artists": [{"name": "Ikkimel"}],
                    },
                }
            )

        result = self._run(
            ["player", "state", "--raw"],
            {"player": SimpleNamespace(state=state)},
        )

        payload = json.loads(result.output)
        self.assertEqual(result.exit_code, 0, result.output)
        self.assertTrue(payload["is_playing"])
        self.assertEqual(payload["item"]["name"], "HAMPELMANN")
        self.assertNotIn("state", payload)

    def test_a_playback_mutation_prints_the_resulting_state(self):
        played = {}

        async def play(**kwargs):
            played.update(kwargs)

        async def state(**kwargs):
            return PlaybackState.model_validate(
                {
                    "is_playing": True,
                    "device": {"name": "Wohnzimmer"},
                    "item": {
                        "type": "track",
                        "name": "HAMPELMANN",
                        "artists": [{"name": "Ikkimel"}],
                    },
                }
            )

        result = self._run(
            ["player", "play", "--uri", "spotify:track:t1"],
            {"player": SimpleNamespace(play=play, state=state)},
        )

        self.assertEqual(result.exit_code, 0, result.output)
        rows = json.loads(result.output)
        self.assertEqual(
            rows,
            [
                {
                    "state": "playing",
                    "track": "HAMPELMANN",
                    "artists": ["Ikkimel"],
                    "device": "Wohnzimmer",
                }
            ],
        )
        self.assertEqual(played["uris"], ["spotify:track:t1"])

    def test_get_accepts_many_ids_in_one_call(self):
        calls = []

        async def get_many(ids, **kwargs):
            calls.append(list(ids))
            return [{"id": item_id, "name": item_id} for item_id in ids]

        result = self._run(
            ["tracks", "get", "a,b", "c"],
            {"tracks": SimpleNamespace(get_many=get_many)},
        )

        self.assertEqual(result.exit_code, 0, result.output)
        self.assertEqual(calls, [["a", "b", "c"]])
        self.assertEqual(len(json.loads(result.output)), 3)

    def test_top_level_play_resolves_then_plays(self):
        played = {}

        async def find(query, **kwargs):
            find.query = query
            return SimpleNamespace(items=[SimpleNamespace(uri="spotify:track:t1")])

        async def play(**kwargs):
            played.update(kwargs)

        async def state(**kwargs):
            return PlaybackState.model_validate(
                {
                    "is_playing": True,
                    "device": {"name": "Wohnzimmer"},
                    "item": {
                        "type": "track",
                        "name": "WHO'S THAT",
                        "artists": [{"name": "Ikkimel"}],
                    },
                }
            )

        result = self._run(
            ["play", "--artist", "Ikkimel", "--track", "WHO'S THAT"],
            {
                "tracks": SimpleNamespace(find=find),
                "player": SimpleNamespace(play=play, state=state),
            },
        )

        self.assertEqual(result.exit_code, 0, result.output)
        self.assertEqual(find.query, 'track:"WHO\'S THAT" artist:"Ikkimel"')
        self.assertEqual(played["uris"], ["spotify:track:t1"])
        self.assertEqual(json.loads(result.output)[0]["track"], "WHO'S THAT")

    def test_play_waits_for_the_requested_track_not_the_previous_one(self):
        # Spotify applies playback asynchronously, so the first read can still
        # describe whatever was playing before.
        states = [
            {
                "is_playing": True,
                "device": {"name": "Wohnzimmer"},
                "item": {
                    "type": "track",
                    "name": "Amber Dusk",
                    "uri": "spotify:track:old",
                    "artists": [{"name": "Caelestis Nati"}],
                },
            },
            {
                "is_playing": True,
                "device": {"name": "Wohnzimmer"},
                "item": {
                    "type": "track",
                    "name": "HAMPELMANN",
                    "uri": "spotify:track:new",
                    "artists": [{"name": "Ikkimel"}],
                },
            },
        ]

        async def play(**kwargs):
            pass

        async def state(**kwargs):
            return PlaybackState.model_validate(states.pop(0) if states else states)

        with patch("spotifyify.cli._core.SETTLE_DELAY_SECONDS", 0):
            result = self._run(
                ["player", "play", "--uri", "spotify:track:new"],
                {"player": SimpleNamespace(play=play, state=state)},
            )

        self.assertEqual(result.exit_code, 0, result.output)
        self.assertEqual(json.loads(result.output)[0]["track"], "HAMPELMANN")

    def test_no_wait_reports_immediately(self):
        reads = []

        async def play(**kwargs):
            pass

        async def state(**kwargs):
            reads.append(1)
            return PlaybackState.model_validate(
                {"is_playing": True, "item": {"type": "track", "name": "Old"}}
            )

        result = self._run(
            ["player", "play", "--uri", "spotify:track:new", "--no-wait"],
            {"player": SimpleNamespace(play=play, state=state)},
        )

        self.assertEqual(result.exit_code, 0, result.output)
        self.assertEqual(len(reads), 1)

    def test_top_level_play_needs_something_to_search_for(self):
        result = self._run(["play"], {})

        self.assertNotEqual(result.exit_code, 0)

    def test_unknown_command_names_the_alternatives(self):
        result = self.runner.invoke(cli.app, ["artists", "lookup"])

        self.assertNotEqual(result.exit_code, 0)
        self.assertIn("Available:", result.output)
        self.assertIn("top-tracks", result.output)

    def test_output_carries_no_ansi_escapes(self):
        async def find(query, **kwargs):
            return {"items": [{"id": "t1", "name": "Track"}]}

        result = self._run(
            ["tracks", "search", "x", "--format", "table"],
            {"tracks": SimpleNamespace(find=find)},
        )

        self.assertEqual(result.exit_code, 0, result.output)
        self.assertNotIn("\x1b", result.output)


if __name__ == "__main__":
    unittest.main()
