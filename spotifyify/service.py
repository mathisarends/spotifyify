import asyncio
from functools import wraps
from typing import Any

import spotipy
from spotipy.oauth2 import SpotifyOAuth

from spotifyify.credentials import SpotifyCredentials
from spotifyify.schemas import (
    DevicesResponse,
    PlaybackState,
    RecentlyPlayedResponse,
    SearchResponse,
    SavedTracksResponse,
    PlaylistsResponse,
    Playlist,
    ShowsSearchResult,
    EpisodesResponse,
    TopTracksResponse,
    TopArtistsResponse,
    Artist,
    AlbumDetails,
    AlbumTracksResponse,
    QueueResponse,
    SavedShowsResponse,
    SavedAlbumsResponse,
    NewReleasesResponse,
    CurrentlyPlayingResponse,
)


class AsyncSpotify:
    def __init__(
        self,
        credentials: SpotifyCredentials,
        scopes: list[str] | None = None,
        requests_timeout: int = 5,
        language: str | None = None,
    ) -> None:
        self._client = spotipy.Spotify(
            auth_manager=SpotifyOAuth(
                client_id=credentials.spotify_client_id,
                client_secret=credentials.spotify_client_secret,
                redirect_uri=credentials.spotify_redirect_uri,
                scope=" ".join(scopes or []),
            ),
            requests_timeout=requests_timeout,
            language=language,
        )
        self._user_id: str | None = None

    async def _get_user_id(self) -> str:
        if self._user_id is None:
            user = await asyncio.to_thread(self._client.current_user)
            self._user_id = user["id"]
        return self._user_id

    async def current_playback(
        self,
        market: str | None = None,
        additional_types: str | None = None,
    ) -> PlaybackState | None:
        result = await asyncio.to_thread(
            self._client.current_playback,
            market=market,
            additional_types=additional_types,
        )
        return PlaybackState.model_validate(result) if result else None

    async def devices(self) -> DevicesResponse:
        result = await asyncio.to_thread(self._client.devices)
        return DevicesResponse.model_validate(result)

    async def start_playback(
        self,
        device_id: str | None = None,
        context_uri: str | None = None,
        uris: list[str] | None = None,
        offset: dict[str, int | str] | None = None,
        position_ms: int | None = None,
    ) -> None:
        return await asyncio.to_thread(
            self._client.start_playback,
            device_id=device_id,
            context_uri=context_uri,
            uris=uris,
            offset=offset,
            position_ms=position_ms,
        )

    async def add_to_queue(
        self,
        uri: str,
        device_id: str | None = None,
    ) -> None:
        return await asyncio.to_thread(
            self._client.add_to_queue,
            uri=uri,
            device_id=device_id,
        )

    async def volume(
        self,
        volume_percent: int,
        device_id: str | None = None,
    ) -> None:
        return await asyncio.to_thread(
            self._client.volume,
            volume_percent=volume_percent,
            device_id=device_id,
        )

    async def transfer_playback(
        self,
        device_id: str,
        force_play: bool = True,
    ) -> None:
        return await asyncio.to_thread(
            self._client.transfer_playback,
            device_id=device_id,
            force_play=force_play,
        )

    async def pause_playback(
        self,
        device_id: str | None = None,
    ) -> None:
        return await asyncio.to_thread(
            self._client.pause_playback,
            device_id=device_id,
        )

    async def next_track(
        self,
        device_id: str | None = None,
    ) -> None:
        return await asyncio.to_thread(
            self._client.next_track,
            device_id=device_id,
        )

    async def previous_track(
        self,
        device_id: str | None = None,
    ) -> None:
        return await asyncio.to_thread(
            self._client.previous_track,
            device_id=device_id,
        )

    async def shuffle(
        self,
        state: bool,
        device_id: str | None = None,
    ) -> None:
        return await asyncio.to_thread(
            self._client.shuffle,
            state=state,
            device_id=device_id,
        )

    async def search(
        self,
        q: str,
        limit: int = 10,
        offset: int = 0,
        type: str = "track",
        market: str | None = None,
    ) -> SearchResponse:
        result = await asyncio.to_thread(
            self._client.search,
            q=q,
            limit=limit,
            offset=offset,
            type=type,
            market=market,
        )
        return SearchResponse.model_validate(result)

    async def current_user_recently_played(
        self,
        limit: int = 50,
        after: int | None = None,
        before: int | None = None,
    ) -> RecentlyPlayedResponse:
        result = await asyncio.to_thread(
            self._client.current_user_recently_played,
            limit=limit,
            after=after,
            before=before,
        )
        return RecentlyPlayedResponse.model_validate(result)

    async def create_playlist(
        self,
        name: str,
        description: str | None = None,
        public: bool = True,
    ) -> Playlist:
        user_id = await self._get_user_id()
        result = await asyncio.to_thread(
            self._client.user_playlist_create,
            user=user_id,
            name=name,
            public=public,
            description=description,
        )
        return Playlist.model_validate(result)

    async def add_tracks_to_playlist(
        self,
        playlist_id: str,
        uris: list[str],
    ) -> None:
        return await asyncio.to_thread(
            self._client.playlist_add_items,
            playlist_id=playlist_id,
            items=uris,
        )

    async def remove_tracks_from_playlist(
        self,
        playlist_id: str,
        uris: list[str],
    ) -> None:
        return await asyncio.to_thread(
            self._client.playlist_remove_all_occurrences_of_items,
            playlist_id=playlist_id,
            items=uris,
        )

    async def get_user_playlists(
        self,
        limit: int = 50,
        offset: int = 0,
    ) -> PlaylistsResponse:
        result = await asyncio.to_thread(
            self._client.current_user_playlists,
            limit=limit,
            offset=offset,
        )
        return PlaylistsResponse.model_validate(result)

    async def search_shows(
        self,
        q: str,
        limit: int = 10,
        offset: int = 0,
        market: str | None = None,
    ) -> ShowsSearchResult:
        result = await asyncio.to_thread(
            self._client.search,
            q=q,
            type="show",
            limit=limit,
            offset=offset,
            market=market,
        )
        shows = result.get("shows", {})
        return ShowsSearchResult.model_validate(shows)

    async def get_show_episodes(
        self,
        show_id: str,
        limit: int = 50,
        offset: int = 0,
    ) -> EpisodesResponse:
        result = await asyncio.to_thread(
            self._client.show_episodes,
            show_id=show_id,
            limit=limit,
            offset=offset,
        )
        return EpisodesResponse.model_validate(result)

    async def get_saved_tracks(
        self,
        limit: int = 20,
        offset: int = 0,
    ) -> SavedTracksResponse:
        result = await asyncio.to_thread(
            self._client.current_user_saved_tracks,
            limit=limit,
            offset=offset,
        )
        return SavedTracksResponse.model_validate(result)

    async def save_tracks(
        self,
        uris: list[str],
    ) -> None:
        return await asyncio.to_thread(
            self._client.current_user_saved_tracks_add,
            tracks=uris,
        )

    async def remove_saved_tracks(
        self,
        uris: list[str],
    ) -> None:
        return await asyncio.to_thread(
            self._client.current_user_saved_tracks_delete,
            tracks=uris,
        )

    async def is_track_saved(
        self,
        uri: str,
    ) -> bool:
        track_id = uri.split(":")[-1] if ":" in uri else uri
        result = await asyncio.to_thread(
            self._client.current_user_saved_tracks_contains,
            tracks=[track_id],
        )
        return result[0] if result else False

    async def get_top_tracks(
        self,
        time_range: str = "medium_term",
        limit: int = 20,
        offset: int = 0,
    ) -> TopTracksResponse:
        result = await asyncio.to_thread(
            self._client.current_user_top_tracks,
            time_range=time_range,
            limit=limit,
            offset=offset,
        )
        return TopTracksResponse.model_validate(result)

    async def get_top_artists(
        self,
        time_range: str = "medium_term",
        limit: int = 20,
        offset: int = 0,
    ) -> TopArtistsResponse:
        result = await asyncio.to_thread(
            self._client.current_user_top_artists,
            time_range=time_range,
            limit=limit,
            offset=offset,
        )
        return TopArtistsResponse.model_validate(result)

    async def get_artist(
        self,
        artist_id: str,
    ) -> Artist:
        result = await asyncio.to_thread(
            self._client.artist,
            artist_id=artist_id,
        )
        return Artist.model_validate(result)

    async def get_artist_top_tracks(
        self,
        artist_id: str,
        market: str | None = None,
    ) -> list:
        result = await asyncio.to_thread(
            self._client.artist_top_tracks,
            artist_id=artist_id,
            market=market,
        )
        return result.get("tracks", [])

    async def get_album(
        self,
        album_id: str,
    ) -> AlbumDetails:
        result = await asyncio.to_thread(
            self._client.album,
            album_id=album_id,
        )
        return AlbumDetails.model_validate(result)

    async def set_repeat(
        self,
        state: str,
        device_id: str | None = None,
    ) -> None:
        if state not in ["off", "track", "context"]:
            raise ValueError("state must be 'off', 'track', or 'context'")
        return await asyncio.to_thread(
            self._client.repeat,
            state=state,
            device_id=device_id,
        )

    async def queue(self) -> QueueResponse:
        result = await asyncio.to_thread(self._client.queue)
        return QueueResponse.model_validate(result)

    async def seek_track(
        self,
        position_ms: int,
        device_id: str | None = None,
    ) -> None:
        return await asyncio.to_thread(
            self._client.seek_track,
            position_ms=position_ms,
            device_id=device_id,
        )

    async def get_saved_shows(
        self,
        limit: int = 20,
        offset: int = 0,
    ) -> SavedShowsResponse:
        result = await asyncio.to_thread(
            self._client.current_user_saved_shows,
            limit=limit,
            offset=offset,
        )
        return SavedShowsResponse.model_validate(result)

    async def get_saved_albums(
        self,
        limit: int = 20,
        offset: int = 0,
    ) -> SavedAlbumsResponse:
        result = await asyncio.to_thread(
            self._client.current_user_saved_albums,
            limit=limit,
            offset=offset,
        )
        return SavedAlbumsResponse.model_validate(result)

    async def remove_saved_albums(
        self,
        album_ids: list[str],
    ) -> None:
        return await asyncio.to_thread(
            self._client.current_user_saved_albums_delete,
            albums=album_ids,
        )

    async def save_albums(
        self,
        album_ids: list[str],
    ) -> None:
        return await asyncio.to_thread(
            self._client.current_user_saved_albums_add,
            albums=album_ids,
        )

    async def is_album_saved(
        self,
        album_id: str,
    ) -> bool:
        result = await asyncio.to_thread(
            self._client.current_user_saved_albums_contains,
            albums=[album_id],
        )
        return result[0] if result else False

    async def album_tracks(
        self,
        album_id: str,
        limit: int = 50,
        offset: int = 0,
    ) -> AlbumTracksResponse:
        result = await asyncio.to_thread(
            self._client.album_tracks,
            album_id=album_id,
            limit=limit,
            offset=offset,
        )
        return AlbumTracksResponse.model_validate(result)

    async def get_playlist(
        self,
        playlist_id: str,
    ) -> Playlist:
        result = await asyncio.to_thread(
            self._client.playlist,
            playlist_id=playlist_id,
        )
        return Playlist.model_validate(result)

    async def change_playlist_details(
        self,
        playlist_id: str,
        name: str | None = None,
        public: bool | None = None,
        collaborative: bool | None = None,
        description: str | None = None,
    ) -> None:
        return await asyncio.to_thread(
            self._client.playlist_change_details,
            playlist_id=playlist_id,
            name=name,
            public=public,
            collaborative=collaborative,
            description=description,
        )

    async def delete_playlist(
        self,
        playlist_id: str,
    ) -> None:
        return await asyncio.to_thread(
            self._client.current_user_unfollow_playlist,
            playlist_id,
        )

    async def get_new_releases(
        self,
        country: str | None = None,
        limit: int = 20,
        offset: int = 0,
    ) -> NewReleasesResponse:
        result = await asyncio.to_thread(
            self._client.new_releases,
            country=country,
            limit=limit,
            offset=offset,
        )
        albums = result.get("albums", {})
        return NewReleasesResponse(
            albums=albums.get("items", []),
            total=albums.get("total", 0),
            limit=albums.get("limit", limit),
            offset=albums.get("offset", offset),
        )

    async def currently_playing(
        self,
        market: str | None = None,
    ) -> CurrentlyPlayingResponse | None:
        result = await asyncio.to_thread(
            self._client.currently_playing,
            market=market,
        )
        return CurrentlyPlayingResponse.model_validate(result) if result else None

    def __getattr__(self, name: str) -> Any:
        """Delegate unknown attributes to wrapped client."""
        attr = getattr(self._client, name)

        if callable(attr):

            @wraps(attr)
            async def async_wrapper(*args: Any, **kwargs: Any) -> Any:
                return await asyncio.to_thread(attr, *args, **kwargs)

            return async_wrapper

        return attr
