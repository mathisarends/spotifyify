from unittest.mock import AsyncMock

import httpx
import pytest

from spotifyify import SpotifyAuthError, SpotifyClient, SpotifyResponseError
from spotifyify.cache_handler import MemoryCacheHandler
from spotifyify.credentials import SpotifyCredentials
from spotifyify.oauth2 import SpotifyOAuth


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "operation",
    [
        lambda client: client.player.devices(),
        lambda client: client.users.following(),
        lambda client: client.playlists.cover_image("p"),
        lambda client: client.users.me(),
    ],
)
async def test_empty_or_wrong_shaped_success_responses_do_not_become_empty_results(
    operation,
):
    async with SpotifyClient(
        transport=httpx.MockTransport(lambda request: httpx.Response(200))
    ) as spotify:
        async with spotify.session(access_token="external"):
            with pytest.raises(SpotifyResponseError):
                await operation(spotify)


@pytest.mark.asyncio
async def test_revoked_environment_refresh_is_not_retried_by_the_next_request():
    calls = []

    def respond(request):
        calls.append(request)
        return httpx.Response(400, json={"error": "invalid_grant"})

    oauth = SpotifyOAuth(
        SpotifyCredentials(
            _env_file=None,
            client_id="app",
            client_secret="secret",
            refresh_token="revoked",
        ),
        MemoryCacheHandler(),
        transport=httpx.MockTransport(respond),
    )
    try:
        for _ in range(2):
            with pytest.raises(SpotifyAuthError):
                await oauth.get_access_token(True)
        assert len(calls) == 1
    finally:
        await oauth.close()


@pytest.mark.asyncio
async def test_injected_provider_does_not_load_unrelated_environment_credentials(
    monkeypatch,
):
    monkeypatch.setenv("SPOTIFY_TOKEN_EXPIRES_AT", "not-a-timestamp")
    async with SpotifyClient(token_provider=AsyncMock()):
        pass


@pytest.mark.asyncio
async def test_complete_pages_require_an_item_collection():
    payload = {
        "href": "https://api.spotify.com/v1/me/tracks",
        "limit": 20,
        "offset": 0,
        "total": 0,
    }
    async with SpotifyClient(
        transport=httpx.MockTransport(lambda request: httpx.Response(200, json=payload))
    ) as spotify:
        async with spotify.session(access_token="external"):
            with pytest.raises(SpotifyResponseError, match="items"):
                await spotify.library.saved_tracks()
