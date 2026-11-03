from unittest.mock import AsyncMock, patch

import httpx
import pytest

from spotifyify import SpotifyClient
from spotifyify.exceptions import (
    SpotifyAPIError,
    SpotifyRateLimitError,
    SpotifyResponseError,
    SpotifyTransportError,
)
from spotifyify.http.retry_policy import HttpMethod, RetryPolicy


@pytest.mark.asyncio
async def test_ambiguous_reorder_failure_is_not_replayed():
    requests = []

    def respond(request):
        requests.append(request)
        return httpx.Response(503, json={"error": {"message": "ambiguous failure"}})

    async with SpotifyClient(
        transport=httpx.MockTransport(respond), retry_backoff_seconds=0
    ) as spotify:
        async with spotify.session(access_token="external"):
            with pytest.raises(SpotifyAPIError):
                await spotify.playlists.reorder("p", range_start=0, insert_before=3)
    assert len(requests) == 1


@pytest.mark.asyncio
async def test_network_and_contract_failures_have_library_error_types():
    def fail(request):
        raise httpx.ConnectError("offline", request=request)

    async with SpotifyClient(transport=httpx.MockTransport(fail)) as spotify:
        async with spotify.session(access_token="external"):
            with pytest.raises(SpotifyTransportError):
                await spotify.tracks.get("t")

    async with SpotifyClient(
        transport=httpx.MockTransport(
            lambda request: httpx.Response(200, text="unexpected")
        )
    ) as spotify:
        async with spotify.session(access_token="external"):
            with pytest.raises(SpotifyResponseError):
                await spotify.tracks.get("t")
            await spotify.player.pause()


@pytest.mark.asyncio
async def test_quota_exhaustion_and_long_retry_after_do_not_loop():
    for payload, headers in [
        ({"error": {"reason": "QUOTA_EXCEEDED"}}, {}),
        ({"error": {"message": "later"}}, {"Retry-After": "3600"}),
    ]:
        transport = httpx.MockTransport(
            lambda request: httpx.Response(429, json=payload, headers=headers)
        )
        hook = AsyncMock()
        async with SpotifyClient(transport=transport) as spotify:
            async with spotify.session(access_token="external", on_retry=hook):
                with pytest.raises(SpotifyRateLimitError):
                    await spotify.tracks.get("t")
        hook.assert_not_awaited()


def test_retry_delays_reject_nonfinite_values_and_cap_backoff():
    policy = RetryPolicy(backoff_seconds=2)
    assert policy.retry_delay(100) == 30
    assert policy.retry_delay(0, retry_after="NaN") == 2
    assert policy.retry_delay(0, retry_after="inf") == 2
    assert not policy.should_retry(HttpMethod.PUT, 503, retry_safe=False)


@pytest.mark.asyncio
async def test_a_rate_limit_cools_other_requests_on_the_same_client():
    seen = []
    hook = AsyncMock()

    def respond(request):
        seen.append(request.url.path)
        return (
            httpx.Response(429, headers={"Retry-After": "0.1"}, json={})
            if len(seen) == 1
            else httpx.Response(200, json={"type": "track"})
        )

    async with SpotifyClient(transport=httpx.MockTransport(respond)) as spotify:
        async with spotify.session(access_token="external", on_retry=hook):
            with patch(
                "spotifyify.http.transport.asyncio.sleep", new_callable=AsyncMock
            ) as sleep:
                await spotify.tracks.get("one")
                await spotify.tracks.get("two")
            assert sleep.await_count == 2
            assert all(0 < call.args[0] <= 0.1 for call in sleep.await_args_list)
    assert len(seen) == 3
