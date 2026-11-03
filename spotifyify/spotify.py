"""Public async Spotify client and its resource namespaces."""

from collections.abc import AsyncIterator, Generator, Iterable
from contextlib import asynccontextmanager, contextmanager
from functools import cached_property
from typing import Self

import httpx

from spotifyify.auth import AccessTokenProvider
from spotifyify.cache_handler import CacheFileHandler, CacheHandler
from spotifyify.client import SpotifyAPIClient
from spotifyify.credentials import SpotifyCredentials
from spotifyify.http import OnRetryHook
from spotifyify.http.context import RequestContext
from spotifyify.namespaces import (
    Albums,
    Artists,
    Episodes,
    Library,
    Player,
    Playlists,
    Shows,
    Tracks,
    Users,
)
from spotifyify.oauth2 import SpotifyOAuth, SpotifyScope


class SpotifyClient:
    """Async Spotify SDK. Use as an async context manager or call ``aclose``.

    An injected token provider remains owned by its caller. The client owns its
    HTTP transport and closes it, including an injected httpx transport.
    """

    def __init__(
        self,
        credentials: SpotifyCredentials | None = None,
        scopes: Iterable[SpotifyScope | str] | None = None,
        cache_handler: CacheHandler | None = None,
        timeout: float = 10.0,
        max_retries: int = 3,
        retry_backoff_seconds: float = 1.0,
        *,
        token_provider: AccessTokenProvider | None = None,
        transport: httpx.AsyncBaseTransport | None = None,
        cache_profile: str = "default",
    ) -> None:
        self._credentials = (
            credentials if credentials is not None else SpotifyCredentials()
        )
        self._scopes = list(scopes or ())
        self._oauth = (
            None
            if token_provider is not None
            else SpotifyOAuth(
                self._credentials,
                cache_handler=cache_handler
                if cache_handler is not None
                else CacheFileHandler(
                    client_id=self._credentials.client_id, profile=cache_profile
                ),
                timeout=timeout,
            )
        )
        provider = token_provider if token_provider is not None else self._oauth
        assert provider is not None
        self._http = SpotifyAPIClient(
            token_provider=provider,
            scopes=self._scopes,
            base_url="https://api.spotify.com/v1",
            timeout=timeout,
            max_retries=max_retries,
            retry_backoff_seconds=retry_backoff_seconds,
            context=self._context,
            transport=transport,
        )

    @cached_property
    def _context(self) -> RequestContext:
        return RequestContext()

    async def __aenter__(self) -> Self:
        await self._http.open()
        return self

    async def __aexit__(self, exc_type, exc, tb) -> None:
        await self.aclose()

    async def aclose(self) -> None:
        try:
            await self._http.close()
        finally:
            if self._oauth is not None:
                await self._oauth.close()

    close = aclose

    @contextmanager
    def retry_hook(self, hook: OnRetryHook) -> Generator[None, None, None]:
        token = self._context.on_retry.set(hook)
        try:
            yield
        finally:
            self._context.on_retry.reset(token)

    @asynccontextmanager
    async def request_context(
        self,
        *,
        access_token: str | None = None,
        on_retry: OnRetryHook | None = None,
    ) -> AsyncIterator[None]:
        """Temporarily set request options for this client and async task."""
        if access_token is not None and not access_token.strip():
            raise ValueError("access_token must not be empty")
        access = (
            self._context.access_token.set(access_token)
            if access_token is not None
            else None
        )
        retry = self._context.on_retry.set(on_retry) if on_retry is not None else None
        try:
            yield
        finally:
            if retry is not None:
                self._context.on_retry.reset(retry)
            if access is not None:
                self._context.access_token.reset(access)

    session = request_context

    @asynccontextmanager
    async def user_token(self, access_token: str) -> AsyncIterator[None]:
        async with self.request_context(access_token=access_token):
            yield

    @property
    def http(self) -> SpotifyAPIClient:
        return self._http

    @cached_property
    def tracks(self) -> Tracks:
        return Tracks(self._http)

    @cached_property
    def artists(self) -> Artists:
        return Artists(self._http)

    @cached_property
    def albums(self) -> Albums:
        return Albums(self._http)

    @cached_property
    def playlists(self) -> Playlists:
        return Playlists(self)

    @cached_property
    def player(self) -> Player:
        return Player(self._http)

    @cached_property
    def library(self) -> Library:
        return Library(self._http)

    @cached_property
    def shows(self) -> Shows:
        return Shows(self._http)

    @cached_property
    def episodes(self) -> Episodes:
        return Episodes(self._http)

    @cached_property
    def users(self) -> Users:
        return Users(self._http)
