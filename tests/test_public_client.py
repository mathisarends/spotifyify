import asyncio
from unittest.mock import AsyncMock

import httpx
import pytest

from spotifyify import SpotifyClient, Spotifyify


@pytest.mark.asyncio
async def test_tokens_and_hooks_are_isolated_between_clients_and_tasks():
    seen = []
    attempts = {}

    def respond(request):
        token = request.headers["Authorization"]
        seen.append(token)
        attempts[token] = attempts.get(token, 0) + 1
        return httpx.Response(
            503 if attempts[token] == 1 else 200, json={"type": "track"}
        )

    provider = AsyncMock()
    provider.get_access_token.return_value = "provider-token"
    first_events, second_events = [], []
    async with SpotifyClient(
        token_provider=provider,
        transport=httpx.MockTransport(respond),
        retry_backoff_seconds=0,
    ) as first:
        async with SpotifyClient(
            token_provider=provider,
            transport=httpx.MockTransport(respond),
            retry_backoff_seconds=0,
        ) as second:
            async with first.request_context(
                access_token="first", on_retry=first_events.append
            ):
                await second.tracks.get("t")
                async with second.request_context(
                    access_token="second", on_retry=second_events.append
                ):
                    await asyncio.gather(first.tracks.get("t"), second.tracks.get("t"))
            assert first._context.access_token.get() is None
            assert second._context.access_token.get() is None
    assert "Bearer provider-token" in seen
    assert len(first_events) == len(second_events) == 1
    assert provider.get_access_token.await_count == 1


@pytest.mark.asyncio
async def test_injected_provider_remains_owned_by_caller_and_closed_client_fails():
    provider = AsyncMock()
    client = SpotifyClient(token_provider=provider)
    assert Spotifyify is SpotifyClient
    assert client.tracks is client.tracks
    await client.aclose()
    await client.aclose()
    provider.close.assert_not_awaited()
    with pytest.raises(RuntimeError, match="closed"):
        await client.tracks.get("t")
