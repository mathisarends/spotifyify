import unittest
from datetime import UTC
from unittest.mock import AsyncMock, patch

import httpx

from spotifyify.http.retry_context import current_retry_hook
from spotifyify.http.retry_policy import HttpMethod, RetryPolicy
from spotifyify.http.transport import HttpTransport


class TestHttpTransport(unittest.IsolatedAsyncioTestCase):
    def _make_transport(self, **policy_kwargs):
        transport = HttpTransport(
            base_url="https://api.spotify.com/v1",
            timeout=10.0,
            retry_policy=RetryPolicy(**policy_kwargs),
        )
        transport._client = AsyncMock(spec=httpx.AsyncClient)
        return transport

    async def test_open_creates_http_client(self):
        transport = HttpTransport(
            base_url="https://api.spotify.com/v1",
            timeout=10.0,
            retry_policy=RetryPolicy(),
        )

        await transport.open()

        self.assertIsNotNone(transport._client)
        await transport.close()

    async def test_close_is_idempotent(self):
        transport = HttpTransport(
            base_url="https://api.spotify.com/v1",
            timeout=10.0,
            retry_policy=RetryPolicy(),
        )

        await transport.close()

    async def test_request_retries_server_error_with_exponential_backoff(self):
        transport = self._make_transport()
        transport._client.request.side_effect = [
            httpx.Response(503),
            httpx.Response(200),
        ]

        with patch(
            "spotifyify.http.transport.asyncio.sleep", new_callable=AsyncMock
        ) as sleep:
            with self.assertLogs("spotifyify.http.transport", level="WARNING") as logs:
                response = await transport.request(
                    HttpMethod.GET,
                    "/tracks",
                    headers={},
                    params=None,
                    json=None,
                    content=None,
                )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(transport._client.request.await_count, 2)
        sleep.assert_awaited_once_with(1.0)
        self.assertIn("status_code=503", logs.output[0])

    async def test_request_honors_retry_after(self):
        transport = self._make_transport()
        transport._client.request.side_effect = [
            httpx.Response(429, headers={"Retry-After": "2.5"}),
            httpx.Response(204),
        ]

        with patch(
            "spotifyify.http.transport.asyncio.sleep", new_callable=AsyncMock
        ) as sleep:
            await transport.request(
                HttpMethod.POST,
                "/playlists/test/items",
                headers={},
                params=None,
                json={"uris": []},
                content=None,
            )

        sleep.assert_awaited_once_with(2.5)

    async def test_request_calls_retry_hook_with_scheduled_retry_details(self):
        transport = self._make_transport(max_retries=2)
        failed_response = httpx.Response(429, headers={"Retry-After": "2.5"})
        transport._client.request.side_effect = [
            failed_response,
            httpx.Response(204),
        ]
        events = []
        token = current_retry_hook.set(events.append)

        try:
            with patch(
                "spotifyify.http.transport.asyncio.sleep", new_callable=AsyncMock
            ):
                await transport.request(
                    HttpMethod.POST,
                    "/playlists/test/items",
                    headers={},
                    params=None,
                    json={"uris": []},
                    content=None,
                )
        finally:
            current_retry_hook.reset(token)

        self.assertEqual(len(events), 1)
        event = events[0]
        self.assertEqual(event.method, HttpMethod.POST)
        self.assertEqual(event.path, "/playlists/test/items")
        self.assertIs(event.response, failed_response)
        self.assertEqual(event.status_code, 429)
        self.assertEqual(event.retry_number, 1)
        self.assertEqual(event.max_retries, 2)
        self.assertEqual(event.retry_in_seconds, 2.5)
        self.assertEqual(event.retry_after, 2.5)
        self.assertEqual(event.retry_at.tzinfo, UTC)

    async def test_request_awaits_async_retry_hook(self):
        transport = self._make_transport()
        transport._client.request.side_effect = [
            httpx.Response(503),
            httpx.Response(200),
        ]
        hook = AsyncMock()
        token = current_retry_hook.set(hook)

        try:
            with patch(
                "spotifyify.http.transport.asyncio.sleep", new_callable=AsyncMock
            ):
                await transport.request(
                    HttpMethod.GET,
                    "/tracks",
                    headers={},
                    params=None,
                    json=None,
                    content=None,
                )
        finally:
            current_retry_hook.reset(token)

        hook.assert_awaited_once()

    async def test_request_does_not_retry_post_server_error(self):
        transport = self._make_transport()
        transport._client.request.return_value = httpx.Response(503)

        with patch(
            "spotifyify.http.transport.asyncio.sleep", new_callable=AsyncMock
        ) as sleep:
            response = await transport.request(
                HttpMethod.POST,
                "/playlists/test/items",
                headers={},
                params=None,
                json={"uris": []},
                content=None,
            )

        self.assertEqual(response.status_code, 503)
        transport._client.request.assert_awaited_once()
        sleep.assert_not_awaited()

    async def test_request_returns_error_after_retry_budget_is_exhausted(self):
        transport = self._make_transport(max_retries=2, backoff_seconds=0.25)
        transport._client.request.return_value = httpx.Response(503)

        with patch(
            "spotifyify.http.transport.asyncio.sleep", new_callable=AsyncMock
        ) as sleep:
            response = await transport.request(
                HttpMethod.GET,
                "/tracks",
                headers={},
                params=None,
                json=None,
                content=None,
            )

        self.assertEqual(response.status_code, 503)
        self.assertEqual(transport._client.request.await_count, 3)
        self.assertEqual(
            [call.args for call in sleep.await_args_list], [(0.25,), (0.5,)]
        )
