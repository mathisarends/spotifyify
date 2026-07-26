import unittest
from types import SimpleNamespace
from unittest.mock import patch

try:
    import typer  # noqa: F401
except ModuleNotFoundError:
    raise unittest.SkipTest("typer is an optional CLI dependency") from None

from spotifyify.cli import quick
from spotifyify.schemas import PlaybackState
from tests.cli_harness import CliTestCase


class TestQueryBuilding(unittest.TestCase):
    def test_filters_are_emitted_in_track_artist_album_order(self):
        query = quick._build_query(
            None, track="WHO'S THAT", artist="Ikkimel", album="Chaos"
        )

        self.assertEqual(query, 'track:"WHO\'S THAT" artist:"Ikkimel" album:"Chaos"')

    def test_free_text_follows_the_filters(self):
        query = quick._build_query(
            ["live", "session"], track=None, artist="Ikkimel", album=None
        )

        self.assertEqual(query, 'artist:"Ikkimel" live session')

    def test_quotes_inside_a_value_cannot_break_out_of_the_filter(self):
        # An unescaped quote would end the filter and turn the rest into free
        # text, silently searching for something else entirely.
        query = quick._build_query(None, track='a" artist:"b', artist=None, album=None)

        self.assertEqual(query, 'track:"a  artist: b"')
        self.assertEqual(query.count('"'), 2)

    def test_surrounding_whitespace_is_trimmed(self):
        self.assertEqual(
            quick._build_query(None, track="  Track  ", artist=None, album=None),
            'track:"Track"',
        )

    def test_nothing_given_produces_an_empty_query(self):
        self.assertEqual(
            quick._build_query(None, track=None, artist=None, album=None), ""
        )
        self.assertEqual(
            quick._build_query([], track=None, artist=None, album=None), ""
        )

    def test_first_hit_of_an_empty_result_is_none(self):
        self.assertIsNone(quick._first(SimpleNamespace(items=[])))
        self.assertIsNone(quick._first(SimpleNamespace(items=None)))
        self.assertIsNone(quick._first(None))


def _playing(name="HAMPELMANN", uri="spotify:track:t1"):
    return PlaybackState.model_validate(
        {
            "is_playing": True,
            "progress_ms": 0,
            "device": {"name": "Wohnzimmer"},
            "item": {
                "type": "track",
                "name": name,
                "uri": uri,
                "artists": [{"name": "Ikkimel"}],
            },
        }
    )


class QuickPlayTestCase(CliTestCase):
    """Records what the top-level play command resolved and started."""

    def namespaces(self, *, tracks=None, albums=None, artists=None):
        self.searched = {}
        self.played = {}

        def finder(kind, hit):
            async def find(query, **kwargs):
                self.searched[kind] = {"query": query, **kwargs}
                return SimpleNamespace(items=[hit] if hit is not None else [])

            return find

        async def play(**kwargs):
            self.played.update(kwargs)

        async def state(**kwargs):
            return _playing()

        return {
            "tracks": SimpleNamespace(find=finder("tracks", tracks)),
            "albums": SimpleNamespace(find=finder("albums", albums)),
            "artists": SimpleNamespace(find=finder("artists", artists)),
            "player": SimpleNamespace(play=play, state=state),
        }


class TestWhatGetsPlayed(QuickPlayTestCase):
    def test_a_track_name_plays_that_one_track(self):
        namespaces = self.namespaces(tracks=SimpleNamespace(uri="spotify:track:t1"))

        self.run_json(["play", "--track", "WHO'S THAT"], namespaces)

        self.assertEqual(self.played["uris"], ["spotify:track:t1"])
        self.assertIsNone(self.played["context_uri"])

    def test_free_text_is_treated_as_a_track_search(self):
        namespaces = self.namespaces(tracks=SimpleNamespace(uri="spotify:track:t1"))

        self.run_json(["play", "hampelmann"], namespaces)

        self.assertEqual(self.searched["tracks"]["query"], "hampelmann")
        self.assertEqual(self.played["uris"], ["spotify:track:t1"])

    def test_an_album_without_a_track_becomes_the_playback_context(self):
        namespaces = self.namespaces(albums=SimpleNamespace(uri="spotify:album:a1"))

        self.run_json(["play", "--album", "Chaos"], namespaces)

        self.assertEqual(self.played["context_uri"], "spotify:album:a1")
        self.assertIsNone(self.played["uris"])
        self.assertNotIn("tracks", self.searched)

    def test_an_artist_alone_becomes_the_playback_context(self):
        namespaces = self.namespaces(artists=SimpleNamespace(uri="spotify:artist:a1"))

        self.run_json(["play", "--artist", "Ikkimel"], namespaces)

        self.assertEqual(self.played["context_uri"], "spotify:artist:a1")
        self.assertIsNone(self.played["uris"])

    def test_a_track_narrowed_by_artist_still_plays_the_track(self):
        namespaces = self.namespaces(tracks=SimpleNamespace(uri="spotify:track:t1"))

        self.run_json(
            ["play", "--artist", "Ikkimel", "--track", "WHO'S THAT"], namespaces
        )

        self.assertEqual(
            self.searched["tracks"]["query"], 'track:"WHO\'S THAT" artist:"Ikkimel"'
        )
        self.assertEqual(self.played["uris"], ["spotify:track:t1"])

    def test_an_album_narrowed_by_free_text_plays_the_track(self):
        # Free text names one thing, so the album is only a filter here.
        namespaces = self.namespaces(tracks=SimpleNamespace(uri="spotify:track:t1"))

        self.run_json(["play", "hampelmann", "--album", "Chaos"], namespaces)

        self.assertEqual(self.searched["tracks"]["query"], 'album:"Chaos" hampelmann')
        self.assertEqual(self.played["uris"], ["spotify:track:t1"])

    def test_only_one_hit_is_fetched(self):
        namespaces = self.namespaces(tracks=SimpleNamespace(uri="spotify:track:t1"))

        self.run_json(["play", "--track", "x"], namespaces)

        self.assertEqual(self.searched["tracks"]["limit"], 1)


class TestQuickPlayFailures(QuickPlayTestCase):
    def test_no_match_exits_four_and_never_starts_playback(self):
        namespaces = self.namespaces(tracks=None)

        result = self.run_cli(["play", "--track", "nothing at all"], namespaces)

        self.assertEqual(result.exit_code, quick.EXIT_NO_MATCH)
        self.assertIn("No match", result.output)
        self.assertEqual(self.played, {})

    def test_an_artist_search_without_a_hit_also_exits_four(self):
        result = self.run_cli(["play", "--artist", "nobody"], self.namespaces())

        self.assertEqual(result.exit_code, quick.EXIT_NO_MATCH)

    def test_nothing_to_search_for_is_a_usage_error(self):
        result = self.run_cli(["play"], self.namespaces())

        self.assertNotEqual(result.exit_code, 0)
        self.assertEqual(self.searched, {})


class TestQuickPlayDefaults(QuickPlayTestCase):
    def test_the_root_market_flag_reaches_the_search(self):
        namespaces = self.namespaces(tracks=SimpleNamespace(uri="spotify:track:t1"))

        self.run_json(["--market", "DE", "play", "--track", "x"], namespaces)

        self.assertEqual(self.searched["tracks"]["market"], "DE")

    def test_the_market_environment_variable_reaches_the_search(self):
        namespaces = self.namespaces(tracks=SimpleNamespace(uri="spotify:track:t1"))

        self.run_json(
            ["play", "--track", "x"], namespaces, env={"SPOTIFYIFY_MARKET": "DE"}
        )

        self.assertEqual(self.searched["tracks"]["market"], "DE")

    def test_the_root_device_flag_targets_playback(self):
        namespaces = self.namespaces(tracks=SimpleNamespace(uri="spotify:track:t1"))

        self.run_json(["--device-id", "kitchen", "play", "--track", "x"], namespaces)

        self.assertEqual(self.played["device_id"], "kitchen")

    def test_an_artist_search_is_not_narrowed_by_market(self):
        # Spotify's artist search takes no market, so passing one would 400.
        namespaces = self.namespaces(artists=SimpleNamespace(uri="spotify:artist:a1"))

        self.run_json(["--market", "DE", "play", "--artist", "Ikkimel"], namespaces)

        self.assertNotIn("market", self.searched["artists"])


class TestQuickPlayReporting(QuickPlayTestCase):
    def test_the_resolved_track_is_reported_not_the_previous_one(self):
        states = [_playing("Amber Dusk", "spotify:track:old"), _playing()]

        async def state(**kwargs):
            return states.pop(0) if len(states) > 1 else states[0]

        namespaces = self.namespaces(tracks=SimpleNamespace(uri="spotify:track:t1"))
        namespaces["player"].state = state

        with patch("spotifyify.cli.core.SETTLE_DELAY_SECONDS", 0):
            rows = self.run_json(["play", "--track", "x"], namespaces)

        self.assertEqual(rows[0]["track"], "HAMPELMANN")

    def test_no_wait_reports_the_first_read(self):
        reads = []

        async def state(**kwargs):
            reads.append(1)
            return _playing("Amber Dusk", "spotify:track:old")

        namespaces = self.namespaces(tracks=SimpleNamespace(uri="spotify:track:t1"))
        namespaces["player"].state = state

        rows = self.run_json(["play", "--track", "x", "--no-wait"], namespaces)

        self.assertEqual(len(reads), 1)
        self.assertEqual(rows[0]["track"], "Amber Dusk")

    def test_playback_columns_are_reported(self):
        namespaces = self.namespaces(tracks=SimpleNamespace(uri="spotify:track:t1"))

        rows = self.run_json(["play", "--track", "x"], namespaces)

        self.assertEqual(list(rows[0]), ["state", "track", "artists", "device"])

    def test_it_asks_for_both_playback_scopes(self):
        from spotifyify import SpotifyScope

        namespaces = self.namespaces(tracks=SimpleNamespace(uri="spotify:track:t1"))

        self.run_json(["play", "--track", "x"], namespaces)

        # Reporting the resulting state needs the read scope alongside modify.
        self.assertEqual(
            set(self.requested_scopes()),
            {
                SpotifyScope.USER_MODIFY_PLAYBACK_STATE,
                SpotifyScope.USER_READ_PLAYBACK_STATE,
            },
        )


if __name__ == "__main__":
    unittest.main()
