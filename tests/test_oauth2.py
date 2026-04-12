import os
import time
import unittest
import unittest.mock


from spotifyify.cache_handler import MemoryCacheHandler
from spotifyify.credentials import SpotifyCredentials
from spotifyify.exceptions import SpotifyAuthError
from spotifyify.oauth2 import SpotifyifyOAuth


def _make_credentials(**env_overrides):
    env = {
        "SPOTIFY_CLIENT_ID": "test_id",
        "SPOTIFY_CLIENT_SECRET": "test_secret",
        "SPOTIFY_REDIRECT_URI": "http://localhost:8080",
    }
    env.update(env_overrides)
    # Remove keys set to None
    env = {k: v for k, v in env.items() if v is not None}
    with unittest.mock.patch.dict(os.environ, env, clear=False):
        return SpotifyCredentials(_env_file=None)


class TestIsTokenExpired(unittest.TestCase):
    def test_expired(self):
        token = {"expires_at": int(time.time()) - 100}
        self.assertTrue(SpotifyifyOAuth._is_token_expired(token))

    def test_not_expired(self):
        token = {"expires_at": int(time.time()) + 3600}
        self.assertFalse(SpotifyifyOAuth._is_token_expired(token))

    def test_expiring_within_buffer(self):
        token = {"expires_at": int(time.time()) + 10}
        self.assertTrue(SpotifyifyOAuth._is_token_expired(token))

    def test_missing_expires_at(self):
        self.assertTrue(SpotifyifyOAuth._is_token_expired({}))


class TestScopeSubset(unittest.TestCase):
    def test_none_required(self):
        self.assertTrue(SpotifyifyOAuth._scope_subset(None, "user-read-playback-state"))

    def test_empty_required(self):
        self.assertTrue(SpotifyifyOAuth._scope_subset("", "some-scope"))

    def test_subset_match(self):
        self.assertTrue(
            SpotifyifyOAuth._scope_subset(
                "user-read-playback-state",
                "user-read-playback-state user-library-read",
            )
        )

    def test_not_subset(self):
        self.assertFalse(
            SpotifyifyOAuth._scope_subset(
                "user-modify-playback-state", "user-read-playback-state"
            )
        )

    def test_none_granted(self):
        self.assertFalse(SpotifyifyOAuth._scope_subset("some-scope", None))


class TestNormalizeScope(unittest.TestCase):
    def setUp(self):
        creds = _make_credentials()
        self.oauth = SpotifyifyOAuth(creds)

    def test_none(self):
        self.assertIsNone(self.oauth._normalize_scope(None))

    def test_string(self):
        result = self.oauth._normalize_scope("b a c")
        self.assertEqual(result, "a b c")

    def test_string_with_commas(self):
        result = self.oauth._normalize_scope("b,a,c")
        self.assertEqual(result, "a b c")

    def test_list(self):
        result = self.oauth._normalize_scope(["c", "a", "b"])
        self.assertEqual(result, "a b c")

    def test_tuple(self):
        result = self.oauth._normalize_scope(("z", "a"))
        self.assertEqual(result, "a z")

    def test_deduplicates(self):
        result = self.oauth._normalize_scope(["a", "a", "b"])
        self.assertEqual(result, "a b")

    def test_empty_string_returns_none(self):
        self.assertIsNone(self.oauth._normalize_scope(""))

    def test_empty_list_returns_none(self):
        self.assertIsNone(self.oauth._normalize_scope([]))

    def test_invalid_type_raises(self):
        with self.assertRaises(TypeError):
            self.oauth._normalize_scope(42)


class TestClientAuthHeader(unittest.TestCase):
    def test_returns_basic_auth(self):
        creds = _make_credentials()
        oauth = SpotifyifyOAuth(creds)
        header = oauth._client_auth_header()
        self.assertIn("Authorization", header)
        self.assertTrue(header["Authorization"].startswith("Basic "))

    def test_missing_client_id_raises(self):
        creds = _make_credentials(SPOTIFY_CLIENT_ID=None)
        oauth = SpotifyifyOAuth(creds)
        with self.assertRaises(SpotifyAuthError):
            oauth._client_auth_header()

    def test_missing_client_secret_raises(self):
        creds = _make_credentials(SPOTIFY_CLIENT_SECRET=None)
        oauth = SpotifyifyOAuth(creds)
        with self.assertRaises(SpotifyAuthError):
            oauth._client_auth_header()


class TestCachedToken(unittest.TestCase):
    def test_returns_from_credentials_access_token(self):
        creds = _make_credentials(
            SPOTIFY_ACCESS_TOKEN="my_token",
            SPOTIFY_TOKEN_EXPIRES_AT="9999999999",
        )
        oauth = SpotifyifyOAuth(creds)
        token = oauth._cached_token()
        self.assertEqual(token["access_token"], "my_token")
        self.assertEqual(token["expires_at"], 9999999999)

    def test_returns_from_cache_handler(self):
        creds = _make_credentials()
        cached = {"access_token": "cached_tok", "expires_at": 9999999999}
        handler = MemoryCacheHandler(token_info=cached)
        oauth = SpotifyifyOAuth(creds, cache_handler=handler)
        token = oauth._cached_token()
        self.assertEqual(token["access_token"], "cached_tok")

    def test_returns_none_when_nothing_cached(self):
        creds = _make_credentials()
        oauth = SpotifyifyOAuth(creds)
        self.assertIsNone(oauth._cached_token())


class TestGetAccessToken(unittest.IsolatedAsyncioTestCase):
    async def test_returns_cached_unexpired_token(self):
        creds = _make_credentials(
            SPOTIFY_ACCESS_TOKEN="valid_token",
            SPOTIFY_TOKEN_EXPIRES_AT=str(int(time.time()) + 3600),
        )
        oauth = SpotifyifyOAuth(creds)
        token = await oauth.get_access_token(require_user=True)
        self.assertEqual(token, "valid_token")
        await oauth.close()

    async def test_raises_when_user_required_no_token(self):
        creds = _make_credentials()
        oauth = SpotifyifyOAuth(creds)
        with self.assertRaises(SpotifyAuthError):
            await oauth.get_access_token(require_user=True)
        await oauth.close()


class TestSaveToken(unittest.TestCase):
    def test_updates_credentials_and_cache(self):
        creds = _make_credentials()
        handler = MemoryCacheHandler()
        oauth = SpotifyifyOAuth(creds, cache_handler=handler)

        token_info = {
            "access_token": "new_tok",
            "refresh_token": "new_ref",
            "expires_at": 9999999999,
        }
        oauth._save_token(token_info)

        self.assertEqual(creds.access_token.get_secret_value(), "new_tok")
        self.assertEqual(creds.refresh_token.get_secret_value(), "new_ref")
        self.assertEqual(creds.token_expires_at, 9999999999)
        self.assertEqual(handler.get_cached_token(), token_info)
