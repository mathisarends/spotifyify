from typing import Self

from collections.abc import Iterable

from spotifyify.cache_handler import CacheHandler
from spotifyify.client import SpotifyClient
from spotifyify.credentials import SpotifyCredentials
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
        self._credentials = credentials or SpotifyCredentials()
        self._scopes = [str(scope) for scope in scopes] if scopes else []
        self._oauth = SpotifyifyOAuth(
            self._credentials,
            cache_handler=cache_handler,
            timeout=timeout,
        )
        self._http = SpotifyClient(
            token_provider=self._oauth,
            scopes=self._scopes,
            base_url=self._SPOTIFY_API_BASE_URL,
            timeout=timeout,
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
