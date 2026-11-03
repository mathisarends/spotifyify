import json
from unittest.mock import AsyncMock, patch
from urllib.parse import parse_qs

import httpx2
import pytest

from spotifyify.cache_handler import (
    CacheFileHandler,
    MemoryCacheHandler,
    default_cache_path,
)
from spotifyify.credentials import SpotifyCredentials
from spotifyify.exceptions import SpotifyAuthError
from spotifyify.oauth2 import SpotifyOAuth


def credentials(**overrides):
    return SpotifyCredentials(
        _env_file=None,
        SPOTIFY_CLIENT_ID="app",
        SPOTIFY_CLIENT_SECRET="secret",
        SPOTIFY_REDIRECT_URI="http://127.0.0.1:8888/callback",
        **overrides,
    )


@pytest.mark.asyncio
async def test_explicit_exchange_refresh_and_revocation_use_real_oauth_serialization():
    requests = []

    def respond(request):
        form = parse_qs(request.content.decode())
        requests.append(form)
        if len(requests) == 3:
            return httpx2.Response(
                400, json={"error": "invalid_grant", "error_description": "revoked"}
            )
        return httpx2.Response(
            200,
            json={
                "access_token": f"token-{len(requests)}",
                "expires_in": 3600,
                **(
                    {"refresh_token": "refresh", "scope": "user-library-read"}
                    if len(requests) == 1
                    else {}
                ),
            },
        )

    cache = MemoryCacheHandler()
    oauth = SpotifyOAuth(credentials(), cache, transport=httpx2.MockTransport(respond))
    try:
        await oauth.exchange_code("code", scope="user-library-read")
        assert await oauth.get_access_token(True, "user-library-read") == "token-1"
        oauth._token_info.expires_at = 0
        assert await oauth.get_access_token(True, "user-library-read") == "token-2"
        oauth._token_info.expires_at = 0
        with pytest.raises(SpotifyAuthError, match="auth login"):
            await oauth.get_access_token(True)
        assert cache.get_cached_token() is None
        assert requests[0]["grant_type"] == ["authorization_code"]
        assert requests[1]["refresh_token"] == ["refresh"]
    finally:
        await oauth.close()


def test_redirect_rules_and_profile_separation():
    for uri in ["http://localhost:8888/callback", "http://example.com/callback"]:
        config = credentials()
        config.redirect_uri = uri
        oauth = SpotifyOAuth(config)
        with pytest.raises(SpotifyAuthError):
            oauth.authorization_url(state="state")
    for uri in [
        "http://127.0.0.1:8888/callback",
        "http://[::1]:8888/callback",
        "https://example.com/callback",
    ]:
        config = credentials()
        config.redirect_uri = uri
        assert "state=state" in SpotifyOAuth(config).authorization_url(state="state")
    assert default_cache_path("app", "one") != default_cache_path("app", "two")
    assert default_cache_path("app", "one") != default_cache_path("other", "one")


def test_cache_replace_failure_preserves_previous_grant_and_cleans_tempfiles(tmp_path):
    cache = CacheFileHandler(tmp_path / "token.json")
    cache.save_token_to_cache({"access_token": "previous"})
    with patch(
        "spotifyify.cache_handler.os.replace", side_effect=OSError("disk failure")
    ):
        with pytest.raises(OSError):
            cache.save_token_to_cache({"access_token": "next"})
    assert cache.get_cached_token()["access_token"] == "previous"
    assert list(tmp_path.iterdir()) == [cache.cache_path]
    cache.cache_path.write_text("[]")
    assert cache.get_cached_token() is None


def test_login_keeps_stdout_json_and_does_not_reveal_tokens():
    pytest.importorskip("typer")
    from typer.testing import CliRunner

    from spotifyify.cli import app

    oauth = SpotifyOAuth(credentials(), MemoryCacheHandler())
    oauth._request_token = AsyncMock(
        return_value={
            "access_token": "never-print-this",
            "refresh_token": "nor-this",
            "scope": "user-library-read",
            "expires_at": 9999999999,
        }
    )

    async def capture(*args, on_ready, **kwargs):
        on_ready()
        return "code"

    with (
        patch("spotifyify.cli.auth._provider", return_value=oauth),
        patch("spotifyify.cli.auth.capture_local_code", side_effect=capture),
    ):
        result = CliRunner().invoke(
            app, ["auth", "login", "--no-browser", "--scope", "user-library-read"]
        )
    assert result.exit_code == 0, result.output
    assert json.loads(result.stdout)[0]["authenticated"] is True
    assert "https://accounts.spotify.com/authorize" in result.stderr
    assert "never-print-this" not in result.output
    assert "nor-this" not in result.output
