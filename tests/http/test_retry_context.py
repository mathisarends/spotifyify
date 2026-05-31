import asyncio
import unittest

from spotifyify.http.retry_context import current_retry_hook
from spotifyify.spotifyify import Spotifyify


class TestRetryContext(unittest.IsolatedAsyncioTestCase):
    async def test_retry_hook_is_isolated_between_concurrent_tasks(self):
        spotify = Spotifyify.__new__(Spotifyify)
        hooks_seen = []

        async def capture_hook(hook):
            with spotify.retry_hook(hook):
                await asyncio.sleep(0)
                hooks_seen.append(current_retry_hook.get())

        def first_hook(event):
            pass

        def second_hook(event):
            pass

        await asyncio.gather(
            capture_hook(first_hook),
            capture_hook(second_hook),
        )

        self.assertCountEqual(hooks_seen, [first_hook, second_hook])
        self.assertIsNone(current_retry_hook.get())

    async def test_retry_hook_restores_previous_hook(self):
        spotify = Spotifyify.__new__(Spotifyify)

        def first_hook(event):
            pass

        def second_hook(event):
            pass

        with spotify.retry_hook(first_hook):
            self.assertIs(current_retry_hook.get(), first_hook)
            with spotify.retry_hook(second_hook):
                self.assertIs(current_retry_hook.get(), second_hook)
            self.assertIs(current_retry_hook.get(), first_hook)

        self.assertIsNone(current_retry_hook.get())
