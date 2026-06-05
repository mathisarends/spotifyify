import asyncio
import unittest

from spotifyify.http.auth_context import current_access_token
from spotifyify.http.retry_context import current_retry_hook
from spotifyify.spotifyify import Spotifyify


class TestAuthContext(unittest.IsolatedAsyncioTestCase):
    async def test_user_token_is_isolated_between_concurrent_tasks(self):
        spotify = Spotifyify.__new__(Spotifyify)
        tokens_seen = []

        async def capture_token(access_token):
            async with spotify.user_token(access_token):
                await asyncio.sleep(0)
                tokens_seen.append(current_access_token.get())

        await asyncio.gather(
            capture_token("first-token"),
            capture_token("second-token"),
        )

        self.assertCountEqual(tokens_seen, ["first-token", "second-token"])
        self.assertIsNone(current_access_token.get())

    async def test_user_token_restores_previous_token(self):
        spotify = Spotifyify.__new__(Spotifyify)

        async with spotify.user_token("first-token"):
            self.assertEqual(current_access_token.get(), "first-token")
            async with spotify.user_token("second-token"):
                self.assertEqual(current_access_token.get(), "second-token")
            self.assertEqual(current_access_token.get(), "first-token")

        self.assertIsNone(current_access_token.get())

    async def test_session_restores_previous_context_values(self):
        spotify = Spotifyify.__new__(Spotifyify)

        def first_hook(event):
            pass

        def second_hook(event):
            pass

        async with spotify.session(access_token="first-token", on_retry=first_hook):
            self.assertEqual(current_access_token.get(), "first-token")
            self.assertIs(current_retry_hook.get(), first_hook)

            async with spotify.session(
                access_token="second-token",
                on_retry=second_hook,
            ):
                self.assertEqual(current_access_token.get(), "second-token")
                self.assertIs(current_retry_hook.get(), second_hook)

            self.assertEqual(current_access_token.get(), "first-token")
            self.assertIs(current_retry_hook.get(), first_hook)

        self.assertIsNone(current_access_token.get())
        self.assertIsNone(current_retry_hook.get())
