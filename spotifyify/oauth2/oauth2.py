import base64
import logging
import secrets
import time
import webbrowser
from typing import Any
from urllib.parse import parse_qs, quote, urlparse

import asyncio

from pydantic import SecretStr

from spotifyify.cache_handler import CacheHandler, MemoryCacheHandler
import httpx

from spotifyify.credentials import SpotifyCredentials
from spotifyify.exceptions import SpotifyAuthError
from spotifyify.oauth2.views import TokenFormPayload
from spotifyify.http import parse_response

logger = logging.getLogger(__name__)


class SpotifyifyOAuth:
    _SPOTIFY_OAUTH_AUTHORIZE_URL = "https://accounts.spotify.com/authorize"
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
        self._http = httpx.AsyncClient(timeout=timeout)

    async def close(self) -> None:
        logger.debug("Closing Spotify OAuth HTTP client")
        await self._http.aclose()

    @staticmethod
    def _require_redirect_uri(credentials: SpotifyCredentials) -> str:
        if not credentials.redirect_uri:
            raise SpotifyAuthError(
                "Missing SPOTIFY_REDIRECT_URI for interactive user authorization."
            )
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

    async def _capture_code_from_local_callback(
        self, redirect_uri: str, state: str, timeout: float = 180.0
    ) -> str | None:
        parsed = urlparse(redirect_uri)
        if parsed.scheme != "http" or parsed.hostname not in {"localhost", "127.0.0.1"}:
            logger.debug("OAuth redirect URI does not support a local callback server")
            return None

        host = parsed.hostname
        port = parsed.port or 80
        expected_path = parsed.path or "/"
        code_future: asyncio.Future[str | None] = (
            asyncio.get_running_loop().create_future()
        )

        async def _handler(
            reader: asyncio.StreamReader, writer: asyncio.StreamWriter
        ) -> None:
            try:
                request_line = await reader.readline()
                if not request_line:
                    return

                parts = request_line.decode("utf-8", errors="replace").strip().split()
                if len(parts) < 2:
                    return

                request_target = parts[1]
                parsed_target = urlparse(request_target)

                while True:
                    header_line = await reader.readline()
                    if not header_line or header_line in {b"\r\n", b"\n"}:
                        break

                response_body = "Authorization completed. You can close this window."
                status_line = "HTTP/1.1 200 OK"

                if parsed_target.path == expected_path:
                    query = parse_qs(parsed_target.query)
                    returned_state = query.get("state", [None])[0]
                    code = query.get("code", [None])[0]
                    error = query.get("error", [None])[0]

                    if error:
                        logger.warning(
                            "Spotify OAuth callback reported an error: error=%s",
                            error,
                        )
                        response_body = f"Spotify authorization failed: {error}"
                        status_line = "HTTP/1.1 400 Bad Request"
                        if not code_future.done():
                            code_future.set_exception(
                                SpotifyAuthError(
                                    f"Spotify authorization failed: {error}"
                                )
                            )
                    elif returned_state != state:
                        logger.warning("State mismatch during Spotify OAuth callback")
                        response_body = "State mismatch during OAuth callback."
                        status_line = "HTTP/1.1 400 Bad Request"
                        if not code_future.done():
                            code_future.set_exception(
                                SpotifyAuthError("State mismatch during OAuth callback")
                            )
                    else:
                        logger.info("Received Spotify OAuth callback")
                        if not code_future.done():
                            code_future.set_result(code)

                payload = response_body.encode("utf-8")
                content_length = len(payload)
                writer.write(
                    (
                        f"{status_line}\r\n"
                        "Content-Type: text/plain; charset=utf-8\r\n"
                        f"Content-Length: {content_length}\r\n"
                        "Connection: close\r\n\r\n"
                    ).encode()
                    + payload
                )
                await writer.drain()
            finally:
                writer.close()
                await writer.wait_closed()

        logger.info(
            "Waiting for Spotify OAuth callback: host=%s port=%d path=%s",
            host,
            port,
            expected_path,
        )
        server = await asyncio.start_server(_handler, host=host, port=port)
        try:
            async with server:
                return await asyncio.wait_for(code_future, timeout=timeout)
        except TimeoutError:
            logger.warning("Timed out waiting for Spotify OAuth callback")
            return None

    async def _capture_code_from_user_prompt(self, state: str) -> str:
        logger.info("Waiting for Spotify OAuth redirect URL from user input")
        prompt = (
            "Paste the full redirect URL from your browser after Spotify login:\n> "
        )
        redirect_response = await asyncio.to_thread(input, prompt)
        parsed = urlparse(redirect_response.strip())
        query = parse_qs(parsed.query)
        returned_state = query.get("state", [None])[0]
        code = query.get("code", [None])[0]
        error = query.get("error", [None])[0]

        if error:
            raise SpotifyAuthError(f"Spotify authorization failed: {error}")
        if returned_state != state:
            raise SpotifyAuthError("State mismatch during OAuth callback")
        if not code:
            raise SpotifyAuthError("No authorization code received from redirect URL")
        return code

    async def _request_user_token(self, scope: str | None) -> dict[str, Any]:
        logger.info("Starting interactive Spotify authorization")
        redirect_uri = self._require_redirect_uri(self.credentials)
        state = secrets.token_urlsafe(24)
        authorize_url = self._build_authorize_url(scope=scope, state=state)

        opened = webbrowser.open(authorize_url)
        if not opened:
            logger.warning("Unable to open a browser for Spotify authorization")
            print("Open this URL to authorize Spotify access:")
            print(authorize_url)

        code = await self._capture_code_from_local_callback(redirect_uri, state=state)
        if not code:
            code = await self._capture_code_from_user_prompt(state=state)

        return await self._request_token(
            TokenFormPayload(
                grant_type="authorization_code",
                code=code,
                redirect_uri=redirect_uri,
            )
        )

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
            response = await self._http.post(
                self._SPOTIFY_OAUTH_TOKEN_URL,
                data=form_data,
                headers=headers,
            )
            parsed = parse_response(response)
        except SpotifyAuthError:
            raise
        except Exception as exc:
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
        if self.credentials.access_token:
            logger.debug("Using token from credentials")
            token_info = {
                "access_token": self.credentials.access_token.get_secret_value(),
                "refresh_token": self.credentials.refresh_token.get_secret_value()
                if self.credentials.refresh_token
                else None,
                "expires_at": self.credentials.token_expires_at or 0,
            }
            return token_info
        logger.debug("Looking up token in cache handler")
        return self.cache_handler.get_cached_token()

    def _save_token(self, token_info: dict[str, Any]) -> None:
        logger.debug("Saving Spotify OAuth token")
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
                logger.debug("Using cached Spotify access token")
                return token_info["access_token"]

        refresh_token = None
        if token_info:
            refresh_token = token_info.get("refresh_token")
        elif self.credentials.refresh_token:
            refresh_token = self.credentials.refresh_token.get_secret_value()

        if refresh_token:
            logger.info("Refreshing Spotify access token")
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
            logger.info("Requesting interactive Spotify access token")
            user_token = await self._request_user_token(desired_scope)
            self._save_token(user_token)
            return user_token["access_token"]

        logger.info("Requesting Spotify client credentials token")
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
