from typing import Any, Literal

from collections.abc import Iterable

from spotifyify.cache_handler import CacheHandler
from spotifyify.credentials import SpotifyCredentials
from spotifyify.http.client import JSONResponse, SpotifyAPIHttpClient
from spotifyify.oauth2 import SpotifyifyOAuth
from spotifyify.schemas import (
    Album,
    Artist,
    CurrentlyPlaying,
    Device,
    Paging,
    PlaybackState,
    Playlist,
    Queue,
    SearchResult,
    Show,
)
from spotifyify.util import SPOTIFY_API_BASE_URL
from spotifyify.views import SpotifyScope


class Spotifyify:
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
            self.credentials, cache_handler=cache_handler, timeout=timeout
        )
        self.http = SpotifyAPIHttpClient(
            token_provider=self.oauth,
            scopes=self.scopes,
            base_url=SPOTIFY_API_BASE_URL,
            timeout=timeout,
        )

    async def __aenter__(self) -> "Spotifyify":
        return self

    async def __aexit__(self, exc_type, exc, tb) -> None:
        await self.close()

    async def close(self) -> None:
        await self.http.close()
        await self.oauth.close()

    async def _request(
        self,
        method: str,
        path: str,
        *,
        params: dict[str, Any] | None = None,
        payload: dict[str, Any] | list[Any] | str | None = None,
        require_user: bool = True,
    ) -> JSONResponse:
        return await self.http.request_json(
            method,
            path,
            params=params,
            payload=payload,
            require_user=require_user,
        )

    @staticmethod
    def _coalesce_items(ids_or_uris: Iterable[str]) -> list[str]:
        return [str(v).strip() for v in ids_or_uris if str(v).strip()]

    async def current_user(self) -> dict[str, Any]:
        data = await self._request("GET", "/me")
        return data or {}

    async def current_playback(self, market: str | None = None) -> PlaybackState | None:
        data = await self._request(
            "GET", "/me/player", params={"market": market} if market else None
        )
        return PlaybackState.model_validate(data) if data else None

    async def currently_playing(
        self, market: str | None = None
    ) -> CurrentlyPlaying | None:
        data = await self._request(
            "GET",
            "/me/player/currently-playing",
            params={"market": market} if market else None,
        )
        return CurrentlyPlaying.model_validate(data) if data else None

    async def devices(self) -> list[Device]:
        data = await self._request("GET", "/me/player/devices") or {}
        return [Device.model_validate(item) for item in data.get("devices", [])]

    async def transfer_playback(self, device_id: str, force_play: bool = True) -> None:
        await self._request(
            "PUT",
            "/me/player",
            payload={"device_ids": [device_id], "play": force_play},
        )

    async def start_playback(
        self,
        device_id: str | None = None,
        context_uri: str | None = None,
        uris: list[str] | None = None,
        offset: dict[str, Any] | None = None,
        position_ms: int | None = None,
    ) -> None:
        payload: dict[str, Any] = {}
        if context_uri is not None:
            payload["context_uri"] = context_uri
        if uris is not None:
            payload["uris"] = uris
        if offset is not None:
            payload["offset"] = offset
        if position_ms is not None:
            payload["position_ms"] = position_ms
        params = {"device_id": device_id} if device_id else None
        await self._request("PUT", "/me/player/play", params=params, payload=payload)

    async def pause_playback(self, device_id: str | None = None) -> None:
        await self._request(
            "PUT",
            "/me/player/pause",
            params={"device_id": device_id} if device_id else None,
        )

    async def next_track(self, device_id: str | None = None) -> None:
        await self._request(
            "POST",
            "/me/player/next",
            params={"device_id": device_id} if device_id else None,
        )

    async def previous_track(self, device_id: str | None = None) -> None:
        await self._request(
            "POST",
            "/me/player/previous",
            params={"device_id": device_id} if device_id else None,
        )

    async def set_shuffle(self, state: bool, device_id: str | None = None) -> None:
        params = {"state": str(state).lower()}
        if device_id:
            params["device_id"] = device_id
        await self._request("PUT", "/me/player/shuffle", params=params)

    async def set_repeat(
        self,
        state: Literal["track", "context", "off"],
        device_id: str | None = None,
    ) -> None:
        params = {"state": state}
        if device_id:
            params["device_id"] = device_id
        await self._request("PUT", "/me/player/repeat", params=params)

    async def seek_track(self, position_ms: int, device_id: str | None = None) -> None:
        params = {"position_ms": position_ms}
        if device_id:
            params["device_id"] = device_id
        await self._request("PUT", "/me/player/seek", params=params)

    async def set_volume(
        self, volume_percent: int, device_id: str | None = None
    ) -> None:
        params = {"volume_percent": volume_percent}
        if device_id:
            params["device_id"] = device_id
        await self._request("PUT", "/me/player/volume", params=params)

    async def get_queue(self) -> Queue:
        data = await self._request("GET", "/me/player/queue") or {}
        return Queue.model_validate(data)

    async def add_to_queue(self, uri: str, device_id: str | None = None) -> None:
        params = {"uri": uri}
        if device_id:
            params["device_id"] = device_id
        await self._request("POST", "/me/player/queue", params=params)

    async def search(
        self,
        q: str,
        type: str = "track",
        limit: int = 10,
        offset: int = 0,
        market: str | None = None,
    ) -> SearchResult:
        params: dict[str, Any] = {
            "q": q,
            "type": type,
            "limit": limit,
            "offset": offset,
        }
        if market:
            params["market"] = market
        data = await self._request("GET", "/search", params=params) or {}
        return SearchResult.model_validate(data)

    async def get_saved_tracks(
        self, limit: int = 20, offset: int = 0, market: str | None = None
    ) -> Paging:
        params = {"limit": limit, "offset": offset}
        if market:
            params["market"] = market
        data = await self._request("GET", "/me/tracks", params=params) or {}
        return Paging.model_validate(data)

    async def save_tracks(self, track_ids: Iterable[str]) -> None:
        ids = self._coalesce_items(track_ids)
        await self._request("PUT", "/me/tracks", params={"ids": ",".join(ids)})

    async def remove_saved_tracks(self, track_ids: Iterable[str]) -> None:
        ids = self._coalesce_items(track_ids)
        await self._request("DELETE", "/me/tracks", params={"ids": ",".join(ids)})

    async def is_track_saved(self, track_ids: Iterable[str]) -> list[bool]:
        ids = self._coalesce_items(track_ids)
        data = await self._request(
            "GET", "/me/tracks/contains", params={"ids": ",".join(ids)}
        )
        return [bool(v) for v in (data or [])]

    async def get_saved_albums(
        self, limit: int = 20, offset: int = 0, market: str | None = None
    ) -> Paging:
        params = {"limit": limit, "offset": offset}
        if market:
            params["market"] = market
        data = await self._request("GET", "/me/albums", params=params) or {}
        return Paging.model_validate(data)

    async def save_albums(self, album_ids: Iterable[str]) -> None:
        ids = self._coalesce_items(album_ids)
        await self._request("PUT", "/me/albums", params={"ids": ",".join(ids)})

    async def remove_saved_albums(self, album_ids: Iterable[str]) -> None:
        ids = self._coalesce_items(album_ids)
        await self._request("DELETE", "/me/albums", params={"ids": ",".join(ids)})

    async def is_album_saved(self, album_ids: Iterable[str]) -> list[bool]:
        ids = self._coalesce_items(album_ids)
        data = await self._request(
            "GET", "/me/albums/contains", params={"ids": ",".join(ids)}
        )
        return [bool(v) for v in (data or [])]

    async def get_saved_shows(self, limit: int = 20, offset: int = 0) -> Paging:
        data = (
            await self._request(
                "GET", "/me/shows", params={"limit": limit, "offset": offset}
            )
            or {}
        )
        return Paging.model_validate(data)

    async def get_user_playlists(self, limit: int = 20, offset: int = 0) -> Paging:
        data = (
            await self._request(
                "GET", "/me/playlists", params={"limit": limit, "offset": offset}
            )
            or {}
        )
        return Paging.model_validate(data)

    async def create_playlist(
        self,
        name: str,
        public: bool = False,
        collaborative: bool = False,
        description: str = "",
        user_id: str | None = None,
    ) -> Playlist:
        target_user = user_id
        if not target_user:
            me = await self.current_user()
            target_user = me.get("id")
        data = (
            await self._request(
                "POST",
                f"/users/{target_user}/playlists",
                payload={
                    "name": name,
                    "public": public,
                    "collaborative": collaborative,
                    "description": description,
                },
            )
            or {}
        )
        return Playlist.model_validate(data)

    async def add_tracks_to_playlist(
        self,
        playlist_id: str,
        uris: Iterable[str],
        position: int | None = None,
    ) -> str | None:
        payload: dict[str, Any] = {"uris": self._coalesce_items(uris)}
        if position is not None:
            payload["position"] = position
        data = (
            await self._request(
                "POST", f"/playlists/{playlist_id}/tracks", payload=payload
            )
            or {}
        )
        return data.get("snapshot_id")

    async def remove_tracks_from_playlist(
        self, playlist_id: str, uris: Iterable[str]
    ) -> str | None:
        payload = {"tracks": [{"uri": uri} for uri in self._coalesce_items(uris)]}
        data = (
            await self._request(
                "DELETE", f"/playlists/{playlist_id}/tracks", payload=payload
            )
            or {}
        )
        return data.get("snapshot_id")

    async def delete_playlist(self, playlist_id: str) -> None:
        await self._request("DELETE", f"/playlists/{playlist_id}/followers")

    async def play_playlist(
        self, playlist_id: str, device_id: str | None = None
    ) -> None:
        await self.start_playback(
            device_id=device_id, context_uri=f"spotify:playlist:{playlist_id}"
        )

    async def get_artist(self, artist_id: str) -> Artist:
        data = await self._request("GET", f"/artists/{artist_id}") or {}
        return Artist.model_validate(data)

    async def get_artist_top_tracks(
        self, artist_id: str, market: str = "US"
    ) -> list[dict[str, Any]]:
        data = (
            await self._request(
                "GET", f"/artists/{artist_id}/top-tracks", params={"market": market}
            )
            or {}
        )
        return list(data.get("tracks", []))

    async def get_album(self, album_id: str, market: str | None = None) -> Album:
        data = (
            await self._request(
                "GET",
                f"/albums/{album_id}",
                params={"market": market} if market else None,
            )
            or {}
        )
        return Album.model_validate(data)

    async def album_tracks(
        self, album_id: str, limit: int = 50, offset: int = 0, market: str | None = None
    ) -> Paging:
        params = {"limit": limit, "offset": offset}
        if market:
            params["market"] = market
        data = (
            await self._request("GET", f"/albums/{album_id}/tracks", params=params)
            or {}
        )
        return Paging.model_validate(data)

    async def play_album(self, album_id: str, device_id: str | None = None) -> None:
        await self.start_playback(
            device_id=device_id, context_uri=f"spotify:album:{album_id}"
        )

    async def get_recently_played(
        self,
        limit: int = 20,
        after: int | None = None,
        before: int | None = None,
    ) -> Paging:
        params: dict[str, Any] = {"limit": limit}
        if after is not None:
            params["after"] = after
        if before is not None:
            params["before"] = before
        data = (
            await self._request("GET", "/me/player/recently-played", params=params)
            or {}
        )
        return Paging.model_validate(data)

    async def get_top_tracks(
        self, time_range: str = "medium_term", limit: int = 20, offset: int = 0
    ) -> Paging:
        data = (
            await self._request(
                "GET",
                "/me/top/tracks",
                params={"time_range": time_range, "limit": limit, "offset": offset},
            )
            or {}
        )
        return Paging.model_validate(data)

    async def get_top_artists(
        self, time_range: str = "medium_term", limit: int = 20, offset: int = 0
    ) -> Paging:
        data = (
            await self._request(
                "GET",
                "/me/top/artists",
                params={"time_range": time_range, "limit": limit, "offset": offset},
            )
            or {}
        )
        return Paging.model_validate(data)

    async def get_new_releases(
        self, country: str | None = None, limit: int = 20, offset: int = 0
    ) -> Paging:
        params: dict[str, Any] = {"limit": limit, "offset": offset}
        if country:
            params["country"] = country
        data = await self._request("GET", "/browse/new-releases", params=params) or {}
        albums = data.get("albums", {}) if isinstance(data, dict) else {}
        return Paging.model_validate(albums)

    async def get_show_episodes(
        self,
        show_id: str,
        market: str | None = None,
        limit: int = 20,
        offset: int = 0,
    ) -> Paging:
        params = {"limit": limit, "offset": offset}
        if market:
            params["market"] = market
        data = (
            await self._request("GET", f"/shows/{show_id}/episodes", params=params)
            or {}
        )
        return Paging.model_validate(data)

    async def play_episode(
        self, episode_uri_or_id: str, device_id: str | None = None
    ) -> None:
        uri = (
            episode_uri_or_id
            if episode_uri_or_id.startswith("spotify:episode:")
            else f"spotify:episode:{episode_uri_or_id}"
        )
        await self.start_playback(device_id=device_id, uris=[uri])

    async def get_show(self, show_id: str, market: str | None = None) -> Show:
        data = (
            await self._request(
                "GET",
                f"/shows/{show_id}",
                params={"market": market} if market else None,
            )
            or {}
        )
        return Show.model_validate(data)
