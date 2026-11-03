"""Regression tests for complete token lifecycles rather than isolated helpers."""

import asyncio
import time
from unittest.mock import AsyncMock

import pytest
import pytest_asyncio

from spotifyify.cache_handler import MemoryCacheHandler
from spotifyify.credentials import SpotifyCredentials
from spotifyify.exceptions import SpotifyAuthError
from spotifyify.oauth2 import SpotifyifyOAuth


def user_token(scope="user-library-read", **overrides):
    return {
        "access_token": "user-token",
        "refresh_token": "refresh-token",
        "expires_at": int(time.time()) + 3600,
        "scope": scope,
        **overrides,
    }


@pytest_asyncio.fixture
async def oauth():
    credentials = SpotifyCredentials(_env_file=None)
    provider = SpotifyifyOAuth(credentials, MemoryCacheHandler())
    try:
        yield provider
    finally:
        await provider.close()


@pytest.mark.asyncio
async def test_repeated_scoped_requests_reuse_the_grant(oauth):
    oauth._save_token(user_token())
    oauth._request_token = AsyncMock(side_effect=AssertionError("Unexpected refresh"))
    for _ in range(3):
        assert await oauth.get_access_token(True, "user-library-read") == "user-token"
    assert oauth.credentials.access_token is None


@pytest.mark.asyncio
async def test_public_query_then_private_query_authorizes_a_user(oauth):
    oauth._request_token = AsyncMock(
        return_value={
            "access_token": "app-token",
            "expires_at": int(time.time()) + 3600,
        }
    )
    assert await oauth.get_access_token(False) == "app-token"
    with pytest.raises(SpotifyAuthError, match="User authorization required"):
        await oauth.get_access_token(True)
    oauth._save_token(user_token())
    assert await oauth.get_access_token(True) == "user-token"


@pytest.mark.asyncio
async def test_new_scopes_require_consent_and_preserve_previous_grants(oauth):
    oauth._save_token(user_token())
    oauth._request_token = AsyncMock(
        side_effect=AssertionError("Refresh cannot add scopes")
    )
    with pytest.raises(SpotifyAuthError, match="user-library-modify"):
        await oauth.get_access_token(True, "user-library-modify")
    assert oauth.token_info.scope == "user-library-read"


@pytest.mark.asyncio
async def test_concurrent_requests_share_one_refresh_and_keep_missing_metadata(oauth):
    oauth._save_token(user_token(expires_at=0))

    async def refresh(payload):
        await asyncio.sleep(0)
        return {"access_token": "renewed", "expires_at": int(time.time()) + 3600}

    oauth._request_token = AsyncMock(side_effect=refresh)
    assert (
        await asyncio.gather(
            *(oauth.get_access_token(True, "user-library-read") for _ in range(8))
        )
        == ["renewed"] * 8
    )
    assert oauth._request_token.await_count == 1
    cached = oauth.cache_handler.get_cached_token()
    assert cached["scope"] == "user-library-read"
    assert cached["refresh_token"] == "refresh-token"


@pytest.mark.asyncio
async def test_app_token_is_not_persisted_over_a_user_grant(oauth):
    oauth._request_token = AsyncMock(
        return_value={
            "access_token": "app-token",
            "expires_at": int(time.time()) + 3600,
        }
    )
    await oauth.get_access_token(False, "user-library-modify")
    assert oauth.cache_handler.get_cached_token() is None
    await oauth.get_access_token(False, "user-library-modify")
    assert oauth._request_token.await_count == 1
