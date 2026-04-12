import base64
import time
from typing import Any

from pydantic import BaseModel, SecretStr

from spotifyify.auth.cache_handler import CacheHandler, MemoryCacheHandler
from spotifyify.auth.credentials import SpotifyCredentials
from spotifyify.exceptions import SpotifyAuthError
from spotifyify.http.client import AsyncHttpClient


class TokenFormPayload(BaseModel):
    grant_type: str
    refresh_token: str | None = None


class SpotifyifyOAuth:
    _SPOTIFY_OAUTH_TOKEN_URL = "https://accounts.spotify.com/api/token"

    def __init__(
        self,
        credentials: SpotifyCredentials,
        cache_handler: CacheHandler | None = None,
        timeout: float = 10.0,
    ) -> None:
        self.credentials = credentials
        self.cache_handler = cache_handler or MemoryCacheHandler()
        self.timeout = timeout
        self.http = AsyncHttpClient(timeout=timeout)

    async def close(self) -> None:
        await self.http.close()

    @staticmethod
    def _is_token_expired(token_info: dict[str, Any]) -> bool:
        return int(token_info.get("expires_at", 0)) <= int(time.time()) + 30

    @staticmethod
    def _scope_subset(required_scope: str | None, granted_scope: str | None) -> bool:
        if not required_scope:
            return True
        required = set(required_scope.split())
        granted = set(granted_scope.split()) if granted_scope else set()
        return required <= granted

    def _client_auth_header(self) -> dict[str, str]:
        client_id = self.credentials.client_id
        client_secret = self.credentials.client_secret
        if not client_id or not client_secret:
            raise SpotifyAuthError("Missing SPOTIFY_CLIENT_ID or SPOTIFY_CLIENT_SECRET")
        raw = f"{client_id}:{client_secret.get_secret_value()}".encode("utf-8")
        encoded = base64.b64encode(raw).decode("ascii")
        return {"Authorization": f"Basic {encoded}"}

    async def _request_token(
        self, payload: TokenFormPayload, use_client_auth: bool = True
    ) -> dict[str, Any]:
        headers = {"Content-Type": "application/x-www-form-urlencoded"}
        if use_client_auth:
            headers.update(self._client_auth_header())

        try:
            parsed = await self.http.post_form(
                self._SPOTIFY_OAUTH_TOKEN_URL,
                data=payload,
                headers=headers,
            )
        except Exception as exc:
            raise SpotifyAuthError(f"Token request failed: {exc}") from exc

        if not isinstance(parsed, dict):
            raise SpotifyAuthError("Token request failed: unexpected response shape")

        token_info = parsed
        token_info["expires_at"] = int(time.time()) + int(
            token_info.get("expires_in", 0)
        )
        return token_info

    def _cached_token(self) -> dict[str, Any] | None:
        if self.credentials.access_token:
            token_info = {
                "access_token": self.credentials.access_token.get_secret_value(),
                "refresh_token": self.credentials.refresh_token.get_secret_value()
                if self.credentials.refresh_token
                else None,
                "expires_at": self.credentials.token_expires_at or 0,
            }
            return token_info
        return self.cache_handler.get_cached_token()

    def _save_token(self, token_info: dict[str, Any]) -> None:
        self.cache_handler.save_token_to_cache(token_info)
        access_token = token_info.get("access_token")
        self.credentials.access_token = (
            SecretStr(access_token) if access_token else None
        )
        refresh_token = token_info.get("refresh_token")
        self.credentials.refresh_token = (
            SecretStr(refresh_token) if refresh_token else None
        )
        self.credentials.token_expires_at = token_info.get("expires_at")

    async def get_access_token(
        self,
        require_user: bool,
        scope: str | list[str] | tuple[str, ...] | None = None,
    ) -> str:
        desired_scope = self._normalize_scope(scope)
        token_info = self._cached_token()

        if token_info and not self._is_token_expired(token_info):
            if self._scope_subset(desired_scope, token_info.get("scope")):
                return token_info["access_token"]

        refresh_token = None
        if token_info:
            refresh_token = token_info.get("refresh_token")
        elif self.credentials.refresh_token:
            refresh_token = self.credentials.refresh_token.get_secret_value()

        if refresh_token:
            refreshed = await self._request_token(
                TokenFormPayload(
                    grant_type="refresh_token", refresh_token=refresh_token
                )
            )
            if "refresh_token" not in refreshed:
                refreshed["refresh_token"] = refresh_token
            self._save_token(refreshed)
            return refreshed["access_token"]

        if require_user:
            raise SpotifyAuthError(
                "User token required. Set SPOTIFY_ACCESS_TOKEN or SPOTIFY_REFRESH_TOKEN."
            )

        client_token = await self._request_token(
            TokenFormPayload(grant_type="client_credentials")
        )
        client_token["scope"] = desired_scope
        self._save_token(client_token)
        return client_token["access_token"]

    def _normalize_scope(
        self, scope: str | list[str] | tuple[str, ...] | None
    ) -> str | None:
        if scope is None:
            return None
        if isinstance(scope, str):
            chunks = [part.strip() for part in scope.replace(",", " ").split()]
            return " ".join(sorted(set(filter(None, chunks)))) or None
        if isinstance(scope, (list, tuple)):
            chunks = [str(part).strip() for part in scope]
            return " ".join(sorted(set(filter(None, chunks)))) or None
        raise TypeError("scope must be str, list[str], tuple[str, ...], or None")
