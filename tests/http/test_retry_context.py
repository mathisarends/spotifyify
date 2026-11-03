import asyncio
import unittest

from spotifyify.spotifyify import Spotifyify


class TestRetryContext(unittest.IsolatedAsyncioTestCase):
    async def test_retry_hook_is_isolated_between_concurrent_tasks(self):
        spotify = Spotifyify.__new__(Spotifyify)
        hooks_seen = []

        async def capture_hook(hook):
            with spotify.retry_hook(hook):
                await asyncio.sleep(0)
                hooks_seen.append(spotify._context.on_retry.get())

        def first_hook(event):
            pass

        def second_hook(event):
            pass

        await asyncio.gather(
            capture_hook(first_hook),
            capture_hook(second_hook),
        )

        self.assertCountEqual(hooks_seen, [first_hook, second_hook])
        self.assertIsNone(spotify._context.on_retry.get())

    async def test_retry_hook_restores_previous_hook(self):
        spotify = Spotifyify.__new__(Spotifyify)

        def first_hook(event):
            pass

        def second_hook(event):
            pass

        with spotify.retry_hook(first_hook):
            self.assertIs(spotify._context.on_retry.get(), first_hook)
            with spotify.retry_hook(second_hook):
                self.assertIs(spotify._context.on_retry.get(), second_hook)
            self.assertIs(spotify._context.on_retry.get(), first_hook)

        self.assertIsNone(spotify._context.on_retry.get())
