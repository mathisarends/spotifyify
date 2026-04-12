from __future__ import annotations

from typing import Any, Self

from collections.abc import Iterable

from spotifyify.albums import AlbumsNamespace
from spotifyify.artists import ArtistsNamespace
from spotifyify.auth.cache_handler import CacheHandler
from spotifyify.auth.credentials import SpotifyCredentials
from spotifyify.auth.oauth2 import SpotifyifyOAuth
from spotifyify.episodes import EpisodesNamespace
from spotifyify.http.client import JSONResponse, SpotifyAPIHttpClient
from spotifyify.library import LibraryNamespace
from spotifyify.player import PlayerNamespace
from spotifyify.playlists import PlaylistsNamespace
from spotifyify.schemas import Paging
from spotifyify.shows import ShowsNamespace
from spotifyify.tracks import TracksNamespace
from spotifyify.users import UsersNamespace
from spotifyify.views import SpotifyScope


class Spotifyify:
    _SPOTIFY_API_BASE_URL = "https://api.spotify.com/v1"

    def __init__(
        self,
        credentials: SpotifyCredentials | None = None,
        scopes: Iterable[SpotifyScope | str] | None = None,
        cache_handler: CacheHandler | None = None,
        timeout: float = 10.0,
    ) -> None:
        self.credentials = credentials or SpotifyCredentials()
        self.scopes = [str(scope) for scope in scopes] if scopes else []
        self.oauth = SpotifyifyOAuth(
            self.credentials,
            cache_handler=cache_handler,
            timeout=timeout,
        )
        self.http = SpotifyAPIHttpClient(
            token_provider=self.oauth,
            scopes=self.scopes,
            base_url=self._SPOTIFY_API_BASE_URL,
            timeout=timeout,
        )

        self._tracks: TracksNamespace | None = None
        self._artists: ArtistsNamespace | None = None
        self._albums: AlbumsNamespace | None = None
        self._playlists: PlaylistsNamespace | None = None
        self._player: PlayerNamespace | None = None
        self._library: LibraryNamespace | None = None
        self._shows: ShowsNamespace | None = None
        self._episodes: EpisodesNamespace | None = None
        self._users: UsersNamespace | None = None

    @property
    def tracks(self) -> TracksNamespace:
        if self._tracks is None:
            self._tracks = TracksNamespace(self)
        return self._tracks

    @property
    def artists(self) -> ArtistsNamespace:
        if self._artists is None:
            self._artists = ArtistsNamespace(self)
        return self._artists

    @property
    def albums(self) -> AlbumsNamespace:
        if self._albums is None:
            self._albums = AlbumsNamespace(self)
        return self._albums

    @property
    def playlists(self) -> PlaylistsNamespace:
        if self._playlists is None:
            self._playlists = PlaylistsNamespace(self)
        return self._playlists

    @property
    def player(self) -> PlayerNamespace:
        if self._player is None:
            self._player = PlayerNamespace(self)
        return self._player

    @property
    def library(self) -> LibraryNamespace:
        if self._library is None:
            self._library = LibraryNamespace(self)
        return self._library

    @property
    def shows(self) -> ShowsNamespace:
        if self._shows is None:
            self._shows = ShowsNamespace(self)
        return self._shows

    @property
    def episodes(self) -> EpisodesNamespace:
        if self._episodes is None:
            self._episodes = EpisodesNamespace(self)
        return self._episodes

    @property
    def users(self) -> UsersNamespace:
        if self._users is None:
            self._users = UsersNamespace(self)
        return self._users

    async def __aenter__(self) -> Self:
        await self.http.open()
        return self

    async def __aexit__(self, exc_type, exc, tb) -> None:
        await self.close()

    async def close(self) -> None:
        await self.http.close()
        await self.oauth.close()

    async def next(self, paging_result: Paging | dict[str, Any]) -> JSONResponse:
        next_url = (
            paging_result.next
            if isinstance(paging_result, Paging)
            else str(paging_result.get("next") or "")
        )
        if not next_url:
            return None
        return await self.http.get(next_url, require_user=False)

    async def previous(self, paging_result: Paging | dict[str, Any]) -> JSONResponse:
        previous_url = (
            paging_result.previous
            if isinstance(paging_result, Paging)
            else str(paging_result.get("previous") or "")
        )
        if not previous_url:
            return None
        return await self.http.get(previous_url, require_user=False)
