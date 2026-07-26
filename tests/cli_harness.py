"""Shared harness for CLI tests: drive the real Typer app over a fake client."""

from __future__ import annotations

import json
import unittest
from unittest.mock import patch

from spotifyify import cli


class FakeSpotifyify:
    """Stands in for the real client inside the CLI's async runner."""

    namespaces: dict = {}
    instances: list[FakeSpotifyify] = []

    def __init__(self, **kwargs):
        self.scopes = list(kwargs.get("scopes") or [])
        FakeSpotifyify.instances.append(self)
        for name, value in self.namespaces.items():
            setattr(self, name, value)

    async def __aenter__(self):
        return self

    async def __aexit__(self, *exc_info):
        return False


class CliTestCase(unittest.TestCase):
    """Invokes the installed commands with only the Spotify client replaced."""

    def setUp(self):
        if cli.typer is None:
            self.skipTest("typer is optional")
        from typer.testing import CliRunner

        self.runner = CliRunner()

    def run_cli(self, args, namespaces=None, env=None):
        FakeSpotifyify.namespaces = namespaces or {}
        FakeSpotifyify.instances = []
        with patch("spotifyify.cli.core.Spotifyify", FakeSpotifyify):
            return self.runner.invoke(cli.app, args, env=env)

    def run_json(self, args, namespaces=None, env=None):
        """Run a command that is expected to succeed and parse its JSON."""
        result = self.run_cli(args, namespaces, env=env)
        self.assertEqual(result.exit_code, 0, result.output)
        return json.loads(result.output)

    def requested_scopes(self):
        """Scopes the command asked the client for, in request order."""
        return [scope for client in FakeSpotifyify.instances for scope in client.scopes]
