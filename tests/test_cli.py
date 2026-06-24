import pathlib
import tomllib
import unittest
from unittest.mock import patch

from spotifyify import SpotifyScope
from spotifyify import cli


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
