import json
import unittest
from types import SimpleNamespace
from unittest.mock import patch

try:
    import typer  # noqa: F401
except ModuleNotFoundError:
    raise unittest.SkipTest("typer is an optional CLI dependency") from None

from spotifyify.cli import options
from spotifyify.exceptions import SpotifyAPIError, SpotifyAuthError, SpotifyifyError
from tests.cli_harness import CliTestCase


class TestErrorTranslation(CliTestCase):
    """Expected API failures become exit codes, not tracebacks."""

    def _failing(self, error):
        async def find(query, **kwargs):
            raise error

        return {"tracks": SimpleNamespace(find=find)}

    def test_an_api_error_exits_one_with_the_message_on_stderr(self):
        result = self.run_cli(
            ["tracks", "search", "x"],
            self._failing(SpotifyAPIError(404, "Not found")),
        )

        self.assertEqual(result.exit_code, options.EXIT_API_ERROR)
        self.assertIn("404: Not found", result.output)

    def test_an_auth_error_exits_three_so_callers_can_re_authenticate(self):
        result = self.run_cli(
            ["tracks", "search", "x"],
            self._failing(SpotifyAuthError("token expired")),
        )

        self.assertEqual(result.exit_code, options.EXIT_AUTH_ERROR)
        self.assertIn("token expired", result.output)

    def test_a_rate_limit_error_is_reported_as_an_api_error(self):
        from spotifyify.exceptions import SpotifyRateLimitError

        result = self.run_cli(
            ["tracks", "search", "x"],
            self._failing(SpotifyRateLimitError("slow down", retry_after=1.0)),
        )

        self.assertEqual(result.exit_code, options.EXIT_API_ERROR)

    def test_the_two_error_exit_codes_stay_distinguishable(self):
        self.assertNotEqual(options.EXIT_API_ERROR, options.EXIT_AUTH_ERROR)

    def test_a_failing_command_prints_no_partial_json(self):
        result = self.run_cli(
            ["tracks", "search", "x"],
            self._failing(SpotifyAPIError(500, "boom")),
        )

        self.assertNotIn("[", result.stdout)

    def test_unexpected_errors_are_not_swallowed(self):
        # Only the failures the CLI has a contract for get translated; anything
        # else has to surface instead of masquerading as a clean exit.
        async def find(query, **kwargs):
            raise SpotifyifyError("something unmodelled")

        result = self.run_cli(
            ["tracks", "search", "x"],
            {"tracks": SimpleNamespace(find=find)},
        )

        self.assertIsInstance(result.exception, SpotifyifyError)


class TestFieldSelection(CliTestCase):
    def _tracks(self):
        async def find(query, **kwargs):
            return {
                "items": [
                    {
                        "id": "t1",
                        "name": "Track",
                        "artists": [{"name": "Ikkimel"}],
                        "album": {"name": "Album"},
                        "uri": "spotify:track:t1",
                        "popularity": 73,
                    }
                ]
            }

        return {"tracks": SimpleNamespace(find=find)}

    def test_fields_replace_the_declared_columns(self):
        rows = self.run_json(["tracks", "search", "x", "--field", "id"], self._tracks())

        self.assertEqual(rows, [{"id": "t1"}])

    def test_fields_can_be_repeated_or_comma_separated(self):
        repeated = self.run_json(
            ["tracks", "search", "x", "-f", "id", "-f", "name"], self._tracks()
        )
        joined = self.run_json(
            ["tracks", "search", "x", "-f", "id,name"], self._tracks()
        )

        self.assertEqual(repeated, joined)
        self.assertEqual(list(repeated[0]), ["id", "name"])

    def test_fields_reach_beyond_the_declared_columns(self):
        rows = self.run_json(
            ["tracks", "search", "x", "-f", "popularity"], self._tracks()
        )

        self.assertEqual(rows, [{"popularity": 73}])

    def test_field_order_follows_the_command_line(self):
        rows = self.run_json(["tracks", "search", "x", "-f", "name,id"], self._tracks())

        self.assertEqual(list(rows[0]), ["name", "id"])

    def test_fields_select_from_the_playback_summary_not_the_raw_state(self):
        from spotifyify.schemas import PlaybackState

        async def state(**kwargs):
            return PlaybackState.model_validate(
                {"is_playing": True, "item": {"type": "track", "name": "HAMPELMANN"}}
            )

        rows = self.run_json(
            ["player", "state", "-f", "state,track"],
            {"player": SimpleNamespace(state=state)},
        )

        self.assertEqual(rows, [{"state": "playing", "track": "HAMPELMANN"}])

    def test_raw_output_ignores_the_field_selection(self):
        result = self.run_cli(
            ["tracks", "search", "x", "-f", "id"],
            self._tracks(),
            env={"SPOTIFYIFY_RAW": "1"},
        )

        self.assertEqual(result.exit_code, 0, result.output)
        self.assertIn("popularity", result.output)


class TestPrintResult(unittest.TestCase):
    def test_projection_runs_before_the_columns_are_selected(self):
        printed = []

        with patch.object(options, "print_json", printed.append):
            options.print_result(
                {"is_playing": True},
                columns=("state",),
                project=lambda value: {"state": "playing"},
            )

        self.assertEqual(printed, [[{"state": "playing"}]])

    def test_output_is_valid_json_even_with_no_items(self):
        printed = []

        with patch.object(options, "print_json", printed.append):
            options.print_result({"items": []}, columns=("id",))

        self.assertEqual(printed, [[]])


class TestLimitBounds(CliTestCase):
    def _tracks(self, seen):
        async def find(query, **kwargs):
            seen.update(kwargs)
            return {"items": []}

        return {"tracks": SimpleNamespace(find=find)}

    def test_the_limit_reaches_the_client(self):
        seen = {}

        self.run_json(["tracks", "search", "x", "--limit", "50"], self._tracks(seen))

        self.assertEqual(seen["limit"], 50)

    def test_a_limit_beyond_what_spotify_accepts_is_rejected_before_any_call(self):
        seen = {}

        result = self.run_cli(
            ["tracks", "search", "x", "--limit", "51"], self._tracks(seen)
        )

        self.assertNotEqual(result.exit_code, 0)
        self.assertEqual(seen, {})

    def test_a_zero_limit_is_rejected(self):
        result = self.run_cli(
            ["tracks", "search", "x", "--limit", "0"], self._tracks({})
        )

        self.assertNotEqual(result.exit_code, 0)


class TestOutputEncoding(CliTestCase):
    def test_non_ascii_names_are_emitted_unescaped(self):
        async def find(query, **kwargs):
            return {"items": [{"id": "t1", "name": "Grüße 東京"}]}

        result = self.run_cli(
            ["tracks", "search", "x", "-f", "name"],
            {"tracks": SimpleNamespace(find=find)},
        )

        self.assertEqual(result.exit_code, 0, result.output)
        self.assertIn("Grüße 東京", result.output)
        self.assertEqual(json.loads(result.output)[0]["name"], "Grüße 東京")


if __name__ == "__main__":
    unittest.main()
