import unittest

from spotifyify.oauth2.views import SpotifyScope


class TestSpotifyScope(unittest.TestCase):
    def test_string_value(self):
        self.assertEqual(
            str(SpotifyScope.USER_READ_PLAYBACK_STATE), "user-read-playback-state"
        )

    def test_is_str(self):
        self.assertIsInstance(SpotifyScope.PLAYLIST_MODIFY_PUBLIC, str)

    def test_all_scopes_are_lowercase_hyphenated(self):
        for scope in SpotifyScope:
            self.assertRegex(str(scope), r"^[a-z-]+$")
