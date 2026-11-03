import base64
import logging
import time
from typing import Any
from urllib.parse import quote, urlparse
from ipaddress import ip_address

import asyncio

from pydantic import ValidationError

from spotifyify.cache_handler import CacheHandler, MemoryCacheHandler
import httpx

from spotifyify.credentials import SpotifyCredentials
from spotifyify.exceptions import SpotifyAuthError, SpotifyAPIError
from spotifyify.oauth2.views import TokenFormPayload
from spotifyify.oauth2.token import TokenInfo
from spotifyify.http import parse_response

logger = logging.getLogger(__name__)


class SpotifyOAuth:
    _SPOTIFY_OAUTH_AUTHORIZE_URL = "https://accounts.spotify.com/authorize"
    _SPOTIFY_OAUTH_TOKEN_URL = "https://accounts.spotify.com/api/token"

    def __init__(
        self,
        credentials: SpotifyCredentials,
        cache_handler: CacheHandler | None = None,
        timeout: float = 10.0,
        *,
        transport: httpx.AsyncBaseTransport | None = None,
    ) -> None:
        self.credentials = credentials
        self.cache_handler = cache_handler or MemoryCacheHandler()
        self.timeout = timeout
        self._http: httpx.AsyncClient | None = None
        self._transport = transport
        self._closed = False
        self._token_info: TokenInfo | None = None
        self._app_token: TokenInfo | None = None
        self._cache_loaded = False
        self._token_lock = asyncio.Lock()

    async def close(self) -> None:
        logger.debug("Closing Spotify OAuth HTTP client")
        if self._http is not None:
            await self._http.aclose()
        self._closed = True

    @staticmethod
    def _require_redirect_uri(credentials: SpotifyCredentials) -> str:
        if not credentials.redirect_uri:
            raise SpotifyAuthError(
                "Missing SPOTIFY_REDIRECT_URI for interactive user authorization."
            )
        parsed = urlparse(credentials.redirect_uri)
        try:
            loopback = ip_address(parsed.hostname or "").is_loopback
        except ValueError:
            loopback = False
        if (
            parsed.hostname == "localhost"
            or not parsed.hostname
            or parsed.username
            or parsed.password
            or parsed.fragment
        ):
            raise SpotifyAuthError(
                "Use an HTTPS redirect URI or an explicit loopback IP such as http://127.0.0.1:8888/callback"
            )
        if parsed.scheme != "https" and not (parsed.scheme == "http" and loopback):
            raise SpotifyAuthError("HTTP redirect URIs require an explicit loopback IP")
        return credentials.redirect_uri

    def _build_authorize_url(self, scope: str | None, state: str) -> str:
        client_id = self.credentials.client_id
        redirect_uri = self._require_redirect_uri(self.credentials)
        if not client_id:
            raise SpotifyAuthError("Missing SPOTIFY_CLIENT_ID")

        params = [
            ("response_type", "code"),
            ("client_id", client_id),
            ("redirect_uri", redirect_uri),
            ("state", state),
            ("show_dialog", "true"),
        ]
        if scope:
            params.append(("scope", scope))

        query = "&".join(f"{key}={quote(value, safe='')}" for key, value in params)
        return f"{self._SPOTIFY_OAUTH_AUTHORIZE_URL}?{query}"

    def authorization_url(
        self, *, state: str, scope: str | list[str] | tuple[str, ...] | None = None
    ) -> str:
        """Build a consent URL without opening a browser or reading input."""
        if not state:
            raise ValueError("state must not be empty")
        return self._build_authorize_url(self._normalize_scope(scope), state)

    async def exchange_code(
        self, code: str, *, scope: str | list[str] | tuple[str, ...] | None = None
    ) -> TokenInfo:
        """Exchange an explicitly obtained authorization code and persist its grant."""
        if not code.strip():
            raise ValueError("code must not be empty")
        async with self._token_lock:
            result = await self._request_token(
                TokenFormPayload(
                    grant_type="authorization_code",
                    code=code,
                    redirect_uri=self._require_redirect_uri(self.credentials),
                )
            )
            result.setdefault("scope", self._normalize_scope(scope))
            self._save_token(result)
            assert self._token_info is not None
            return self._token_info

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

        logger.debug(
            "Requesting Spotify OAuth token: grant_type=%s", payload.grant_type
        )
        try:
            form_data = payload.model_dump(mode="json", exclude_none=True)
            if self._closed:
                raise SpotifyAuthError("OAuth provider is closed")
            if self._http is None:
                self._http = httpx.AsyncClient(
                    timeout=self.timeout, transport=self._transport
                )
            response = await self._http.post(
                self._SPOTIFY_OAUTH_TOKEN_URL,
                data=form_data,
                headers=headers,
            )
            parsed = parse_response(response)
        except SpotifyAuthError:
            raise
        except SpotifyAPIError as exc:
            error_code = exc.details.get("error")
            if not isinstance(error_code, str):
                error_code = None
            raise SpotifyAuthError(
                f"Token request failed: {exc.message}", code=error_code
            ) from exc
        except httpx.HTTPError as exc:
            logger.exception(
                "Spotify OAuth token request failed: grant_type=%s",
                payload.grant_type,
            )
            raise SpotifyAuthError(f"Token request failed: {exc}") from exc

        if not isinstance(parsed, dict):
            logger.warning(
                "Spotify OAuth token request returned an unexpected response shape: "
                "grant_type=%s",
                payload.grant_type,
            )
            raise SpotifyAuthError("Token request failed: unexpected response shape")

        logger.debug("Received Spotify OAuth token: grant_type=%s", payload.grant_type)
        token_info = parsed
        token_info["expires_at"] = int(time.time()) + int(
            token_info.get("expires_in", 0)
        )
        return token_info

    def _cached_token(self) -> dict[str, Any] | None:
        if self._cache_loaded:
            return (
                self._token_info.model_dump(exclude_none=True)
                if self._token_info
                else None
            )
        self._cache_loaded = True
        if self.credentials.access_token:
            token_info: Any = {
                "access_token": self.credentials.access_token.get_secret_value(),
                "refresh_token": self.credentials.refresh_token.get_secret_value()
                if self.credentials.refresh_token
                else None,
                "expires_at": self.credentials.token_expires_at,
                "scope": self.credentials.token_scopes,
                "auth_type": "user",
            }
        else:
            token_info = self.cache_handler.get_cached_token()
        if token_info is not None:
            try:
                self._token_info = TokenInfo.model_validate(token_info)
            except ValidationError:
                logger.warning("Ignoring invalid OAuth token cache")
        return (
            self._token_info.model_dump(exclude_none=True) if self._token_info else None
        )

    def _save_token(self, token_info: dict[str, Any]) -> None:
        logger.debug("Saving Spotify OAuth token")
        try:
            self._token_info = TokenInfo.model_validate(
                {**token_info, "auth_type": "user"}
            )
        except ValidationError as exc:
            raise SpotifyAuthError("Invalid OAuth token response") from exc
        self._cache_loaded = True
        self.cache_handler.save_token_to_cache(
            self._token_info.model_dump(exclude_none=True)
        )

    @property
    def token_info(self) -> TokenInfo | None:
        """A copy of the local grant; this does not refresh or authorize."""
        self._cached_token()
        return self._token_info.model_copy(deep=True) if self._token_info else None

    async def get_access_token(
        self,
        require_user: bool,
        scope: str | list[str] | tuple[str, ...] | None = None,
    ) -> str:
        desired_scope = self._normalize_scope(scope)
        async with self._token_lock:
            self._cached_token()
            token = self._token_info
            required_scope = desired_scope if require_user else None
            if token and (not require_user or token.auth_type == "user"):
                if not token.expired and token.permits(required_scope):
                    return token.access_token

            refresh_token = token.refresh_token if token else None
            if not refresh_token and not token and self.credentials.refresh_token:
                refresh_token = self.credentials.refresh_token.get_secret_value()
            # Refreshing never adds permissions. Reauthorize when known grants
            # are insufficient instead of repeatedly refreshing the same grant.
            if refresh_token and (not token or token.permits(required_scope)):
                try:
                    refreshed = await self._request_token(
                        TokenFormPayload(
                            grant_type="refresh_token", refresh_token=refresh_token
                        )
                    )
                except SpotifyAuthError as exc:
                    if exc.code == "invalid_grant":
                        self._token_info = None
                        self.cache_handler.delete_cached_token()
                        raise SpotifyAuthError(
                            "The user grant expired or was revoked. Run spotifyify auth login.",
                            code="invalid_grant",
                        ) from exc
                    raise
                refreshed.setdefault("refresh_token", refresh_token)
                if token and token.scope is not None:
                    refreshed.setdefault("scope", token.scope)
                self._save_token(refreshed)
                if self._token_info and self._token_info.permits(required_scope):
                    return self._token_info.access_token

            if require_user:
                missing = desired_scope or "a user token"
                raise SpotifyAuthError(
                    f"User authorization required ({missing}). Run spotifyify auth login "
                    "with the required --scope options, or supply a user token."
                )

            if self._app_token and not self._app_token.expired:
                return self._app_token.access_token
            client_token = await self._request_token(
                TokenFormPayload(grant_type="client_credentials")
            )
            self._app_token = TokenInfo.model_validate(
                {**client_token, "auth_type": "client_credentials", "scope": ""}
            )
            return self._app_token.access_token

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


SpotifyifyOAuth = SpotifyOAuth
