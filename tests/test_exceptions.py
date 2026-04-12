import unittest

from spotifyify.exceptions import SpotifyAPIError, SpotifyAuthError, SpotifyifyError


class TestExceptions(unittest.TestCase):
    def test_hierarchy(self):
        self.assertTrue(issubclass(SpotifyAPIError, SpotifyifyError))
        self.assertTrue(issubclass(SpotifyAuthError, SpotifyifyError))
        self.assertTrue(issubclass(SpotifyifyError, Exception))

    def test_api_error_attributes(self):
        err = SpotifyAPIError(404, "Not found", {"reason": "missing"})
        self.assertEqual(err.status_code, 404)
        self.assertEqual(err.message, "Not found")
        self.assertEqual(err.details, {"reason": "missing"})
        self.assertIn("404", str(err))
        self.assertIn("Not found", str(err))

    def test_api_error_default_details(self):
        err = SpotifyAPIError(500, "Server error")
        self.assertEqual(err.details, {})

    def test_auth_error(self):
        err = SpotifyAuthError("bad creds")
        self.assertIn("bad creds", str(err))
