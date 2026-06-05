from typing import Any, Self

from collections.abc import AsyncIterator, Iterable, Iterator
from contextlib import asynccontextmanager, contextmanager
from contextvars import ContextVar, Token

from spotifyify.cache_handler import CacheFileHandler, CacheHandler
from spotifyify.client import SpotifyClient
from spotifyify.credentials import SpotifyCredentials
from spotifyify.http import OnRetryHook
from spotifyify.http.auth_context import current_access_token
from spotifyify.http.retry_context import current_retry_hook
from spotifyify.oauth2 import SpotifyifyOAuth

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

from spotifyify.oauth2 import SpotifyScope


class Spotifyify:
    _SPOTIFY_API_BASE_URL = "https://api.spotify.com/v1"

    def __init__(
        self,
        credentials: SpotifyCredentials | None = None,
        scopes: Iterable[SpotifyScope] | None = None,
        cache_handler: CacheHandler | None = None,
        timeout: float = 10.0,
        max_retries: int = 3,
        retry_backoff_seconds: float = 1.0,
    ) -> None:
        self._credentials = credentials or SpotifyCredentials()
        self._scopes = [scope for scope in (scopes or ())]
        self._oauth = SpotifyifyOAuth(
            self._credentials,
            cache_handler=cache_handler or CacheFileHandler(),
            timeout=timeout,
        )
        self._http = SpotifyClient(
            token_provider=self._oauth,
            scopes=self._scopes,
            base_url=self._SPOTIFY_API_BASE_URL,
            timeout=timeout,
            max_retries=max_retries,
            retry_backoff_seconds=retry_backoff_seconds,
        )

        self._tracks: Tracks | None = None
        self._artists: Artists | None = None
        self._albums: Albums | None = None
        self._playlists: Playlists | None = None
        self._player: Player | None = None
        self._library: Library | None = None
        self._shows: Shows | None = None
        self._episodes: Episodes | None = None
        self._users: Users | None = None

    async def __aenter__(self) -> Self:
        await self._http.open()
        return self

    async def __aexit__(self, exc_type, exc, tb) -> None:
        await self.close()

    async def close(self) -> None:
        await self._http.close()
        await self._oauth.close()

    @contextmanager
    def retry_hook(self, hook: OnRetryHook) -> Iterator[None]:
        token = current_retry_hook.set(hook)
        try:
            yield
        finally:
            current_retry_hook.reset(token)

    @asynccontextmanager
    async def session(
        self,
        *,
        access_token: str | None = None,
        on_retry: OnRetryHook | None = None,
    ) -> AsyncIterator[None]:
        """Scope user-specific calls with a supplied token, otherwise use app auth."""
        ctx_tokens: list[tuple[ContextVar[Any], Token[Any]]] = []
        if access_token is not None:
            ctx_tokens.append(
                (current_access_token, current_access_token.set(access_token))
            )
        if on_retry is not None:
            ctx_tokens.append((current_retry_hook, current_retry_hook.set(on_retry)))
        try:
            yield
        finally:
            for context_var, token in reversed(ctx_tokens):
                context_var.reset(token)

    @asynccontextmanager
    async def user_token(self, access_token: str) -> AsyncIterator[None]:
        async with self.session(access_token=access_token):
            yield

    @property
    def http(self) -> SpotifyClient:
        return self._http

    @property
    def tracks(self) -> Tracks:
        if self._tracks is None:
            self._tracks = Tracks(self._http)
        return self._tracks

    @property
    def artists(self) -> Artists:
        if self._artists is None:
            self._artists = Artists(self._http)
        return self._artists

    @property
    def albums(self) -> Albums:
        if self._albums is None:
            self._albums = Albums(self._http)
        return self._albums

    @property
    def playlists(self) -> Playlists:
        if self._playlists is None:
            self._playlists = Playlists(self)
        return self._playlists

    @property
    def player(self) -> Player:
        if self._player is None:
            self._player = Player(self._http)
        return self._player

    @property
    def library(self) -> Library:
        if self._library is None:
            self._library = Library(self._http)
        return self._library

    @property
    def shows(self) -> Shows:
        if self._shows is None:
            self._shows = Shows(self._http)
        return self._shows

    @property
    def episodes(self) -> Episodes:
        if self._episodes is None:
            self._episodes = Episodes(self._http)
        return self._episodes

    @property
    def users(self) -> Users:
        if self._users is None:
            self._users = Users(self._http)
        return self._users
