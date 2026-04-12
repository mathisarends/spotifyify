import os
import unittest
import unittest.mock

from pydantic import SecretStr

from spotifyify.credentials import SpotifyCredentials


class TestSpotifyCredentials(unittest.TestCase):
    def test_defaults_to_none(self):
        creds = SpotifyCredentials(_env_file=None)
        self.assertIsNone(creds.client_id)
        self.assertIsNone(creds.client_secret)
        self.assertIsNone(creds.redirect_uri)
        self.assertIsNone(creds.access_token)
        self.assertIsNone(creds.refresh_token)
        self.assertIsNone(creds.token_expires_at)

    def test_reads_from_env(self):
        env = {
            "SPOTIFY_CLIENT_ID": "cid",
            "SPOTIFY_CLIENT_SECRET": "csec",
            "SPOTIFY_REDIRECT_URI": "http://localhost",
            "SPOTIFY_ACCESS_TOKEN": "atok",
            "SPOTIFY_REFRESH_TOKEN": "rtok",
            "SPOTIFY_TOKEN_EXPIRES_AT": "9999999999",
        }
        with unittest.mock.patch.dict(os.environ, env, clear=False):
            creds = SpotifyCredentials(_env_file=None)
        self.assertEqual(creds.client_id, "cid")
        self.assertIsInstance(creds.client_secret, SecretStr)
        self.assertEqual(creds.client_secret.get_secret_value(), "csec")
        self.assertEqual(creds.redirect_uri, "http://localhost")
        self.assertIsInstance(creds.access_token, SecretStr)
        self.assertEqual(creds.access_token.get_secret_value(), "atok")
        self.assertEqual(creds.refresh_token.get_secret_value(), "rtok")
        self.assertEqual(creds.token_expires_at, 9999999999)
