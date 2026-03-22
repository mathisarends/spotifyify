from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from mcp.server.fastmcp import FastMCP

from spotifyify import AsyncSpotify, SpotifyScope
from spotifyify.credentials import SpotifyCredentials
from spotifyify.device_resolver import DeviceResolver
from spotifyify.schemas import (
    AlbumDetails,
    Artist,
    CurrentlyPlayingResponse,
    DevicesResponse,
    Episode,
    NewReleasesResponse,
    PlaybackState,
    Playlist,
    PlaylistsResponse,
    QueueResponse,
    RecentlyPlayedResponse,
    SavedAlbumsResponse,
    SimplifiedAlbum,
    Track,
)
from spotifyify.views import ActionSuccessResponse

_SPOTIFY_SCOPES = [
    SpotifyScope.USER_READ_PLAYBACK_STATE,
    SpotifyScope.USER_MODIFY_PLAYBACK_STATE,
    SpotifyScope.USER_LIBRARY_READ,
    SpotifyScope.USER_LIBRARY_MODIFY,
    SpotifyScope.USER_TOP_READ,
    SpotifyScope.USER_READ_RECENTLY_PLAYED,
    SpotifyScope.PLAYLIST_MODIFY_PUBLIC,
    SpotifyScope.PLAYLIST_MODIFY_PRIVATE,
    SpotifyScope.PLAYLIST_READ_PRIVATE,
]

_spotify_client: AsyncSpotify | None = None
_device_resolver: DeviceResolver | None = None


@asynccontextmanager
async def lifespan(mcp: FastMCP) -> AsyncIterator[None]:
    global _spotify_client, _device_resolver

    _spotify_client = AsyncSpotify(
        credentials=SpotifyCredentials(),
        scopes=_SPOTIFY_SCOPES,
    )

    _device_resolver = DeviceResolver()
    devices = await _spotify_client.devices()
    for device in devices.devices:
        _device_resolver.set_device(device.name, device.id)

    yield

    if _device_resolver:
        _device_resolver.invalidate()
    _device_resolver = None
    _spotify_client = None


mcp = FastMCP(name="Spotify MCP Server", lifespan=lifespan)


@mcp.tool()
async def get_current_playback(market: str | None = None) -> PlaybackState | None:
    return await _spotify_client.current_playback(market=market)


@mcp.tool(
    description="Get available devices and update the device resolver cache. - use this when u cant find a device."
)
async def get_devices() -> DevicesResponse:
    devices = await _spotify_client.devices()
    for device in devices.devices:
        _device_resolver.set_device(device.name, device.id)
    return devices


@mcp.tool(
    description="""Start or resume playback on a device.
    IMPORTANT: If Spotify is paused or inactive, first call transfer_playback to activate the device,
    then start_playback. Without an active device the API will return a 'No active device' error."""
)
async def start_playback(
    device_name: str | None = None,
    context_uri: str | None = None,
    uris: list[str] | None = None,
) -> ActionSuccessResponse:
    device_id = _device_resolver.resolve(device_name)
    await _spotify_client.start_playback(
        device_id=device_id,
        context_uri=context_uri,
        uris=uris,
    )
    return ActionSuccessResponse(message="Playback started")


@mcp.tool()
async def pause_playback(device_name: str | None = None) -> ActionSuccessResponse:
    device_id = _device_resolver.resolve(device_name)
    await _spotify_client.pause_playback(device_id=device_id)
    return ActionSuccessResponse(message="Playback paused")


@mcp.tool()
async def add_to_queue(
    uri: str, device_name: str | None = None
) -> ActionSuccessResponse:
    device_id = _device_resolver.resolve(device_name)
    await _spotify_client.add_to_queue(uri=uri, device_id=device_id)
    return ActionSuccessResponse(message=f"Added {uri} to queue")


@mcp.tool()
async def set_volume(
    volume_percent: int, device_name: str | None = None
) -> ActionSuccessResponse:
    device_id = _device_resolver.resolve(device_name)
    await _spotify_client.volume(volume_percent=volume_percent, device_id=device_id)
    return ActionSuccessResponse(message=f"Volume set to {volume_percent}%")


@mcp.tool(
    description="""Transfer playback to a device and force it to play.
    Use this BEFORE start_playback if the device is paused or inactive.
    Also use when switching between devices."""
)
async def transfer_playback(device_name: str) -> ActionSuccessResponse:
    device_id = _device_resolver.resolve(device_name)
    if not device_id:
        return ActionSuccessResponse(message=f"Device '{device_name}' not found")
    await _spotify_client.transfer_playback(device_id=device_id, force_play=True)
    return ActionSuccessResponse(
        message=f"Playback transferred to device {device_name}"
    )


@mcp.tool()
async def search_tracks(
    query: str,
    limit: int = 10,
    market: str | None = None,
) -> list[Track]:
    result = await _spotify_client.search(
        q=query, type="track", limit=limit, market=market
    )
    return result.tracks.items if result.tracks else []


@mcp.tool()
async def search_albums(
    query: str,
    limit: int = 10,
    market: str | None = None,
) -> list[SimplifiedAlbum]:
    result = await _spotify_client.search(
        q=query, type="album", limit=limit, market=market
    )
    return result.albums.items if result.albums else []


@mcp.tool()
async def next_track(device_name: str | None = None) -> ActionSuccessResponse:
    device_id = _device_resolver.resolve(device_name)
    await _spotify_client.next_track(device_id=device_id)
    return ActionSuccessResponse(message="Skipped to next track")


@mcp.tool()
async def previous_track(device_name: str | None = None) -> ActionSuccessResponse:
    device_id = _device_resolver.resolve(device_name)
    await _spotify_client.previous_track(device_id=device_id)
    return ActionSuccessResponse(message="Skipped to previous track")


@mcp.tool()
async def set_shuffle(
    state: bool, device_name: str | None = None
) -> ActionSuccessResponse:
    device_id = _device_resolver.resolve(device_name)
    await _spotify_client.shuffle(state=state, device_id=device_id)
    status = "enabled" if state else "disabled"
    return ActionSuccessResponse(message=f"Shuffle {status}")


@mcp.tool()
async def play_album(
    album_uri: str, device_name: str | None = None
) -> ActionSuccessResponse:
    device_id = _device_resolver.resolve(device_name)
    await _spotify_client.start_playback(device_id=device_id, context_uri=album_uri)
    return ActionSuccessResponse(message=f"Playing album {album_uri}")


@mcp.tool()
async def get_recently_played(
    limit: int = 20,
    after: int | None = None,
    before: int | None = None,
) -> RecentlyPlayedResponse:
    return await _spotify_client.current_user_recently_played(
        limit=limit, after=after, before=before
    )


@mcp.tool()
async def create_playlist(
    name: str,
    description: str | None = None,
    public: bool = True,
) -> Playlist:
    return await _spotify_client.create_playlist(
        name=name, description=description, public=public
    )


@mcp.tool()
async def change_playlist_details(
    playlist_id: str,
    name: str | None = None,
    public: bool | None = None,
    collaborative: bool | None = None,
    description: str | None = None,
) -> ActionSuccessResponse:
    await _spotify_client.change_playlist_details(
        playlist_id=playlist_id,
        name=name,
        public=public,
        collaborative=collaborative,
        description=description,
    )
    return ActionSuccessResponse(message=f"Playlist {playlist_id} details updated")


@mcp.tool()
async def add_tracks_to_playlist(
    playlist_id: str,
    uris: list[str],
) -> ActionSuccessResponse:
    await _spotify_client.add_tracks_to_playlist(playlist_id=playlist_id, uris=uris)
    return ActionSuccessResponse(message=f"Added {len(uris)} track(s) to playlist")


@mcp.tool()
async def remove_tracks_from_playlist(
    playlist_id: str,
    uris: list[str],
) -> ActionSuccessResponse:
    await _spotify_client.remove_tracks_from_playlist(
        playlist_id=playlist_id, uris=uris
    )
    return ActionSuccessResponse(message=f"Removed {len(uris)} track(s) from playlist")


@mcp.tool()
async def get_user_playlists(
    limit: int = 50,
    offset: int = 0,
) -> PlaylistsResponse:
    return await _spotify_client.get_user_playlists(limit=limit, offset=offset)


@mcp.tool()
async def play_playlist(
    playlist_uri: str,
    device_name: str | None = None,
) -> ActionSuccessResponse:
    device_id = _device_resolver.resolve(device_name)
    await _spotify_client.start_playback(device_id=device_id, context_uri=playlist_uri)
    return ActionSuccessResponse(message=f"Playing playlist {playlist_uri}")


@mcp.tool()
async def search_shows(
    query: str,
    limit: int = 10,
    market: str | None = None,
) -> list:
    result = await _spotify_client.search_shows(q=query, limit=limit, market=market)
    return result.items if result.items else []


@mcp.tool()
async def get_show_episodes(
    show_id: str,
    limit: int = 50,
    offset: int = 0,
) -> list[Episode]:
    result = await _spotify_client.get_show_episodes(
        show_id=show_id, limit=limit, offset=offset
    )
    return result.items if result.items else []


@mcp.tool()
async def play_episode(
    episode_uri: str,
    device_name: str | None = None,
) -> ActionSuccessResponse:
    device_id = _device_resolver.resolve(device_name)
    await _spotify_client.start_playback(device_id=device_id, uris=[episode_uri])
    return ActionSuccessResponse(message=f"Playing episode {episode_uri}")


@mcp.tool()
async def get_saved_tracks(
    limit: int = 20,
    offset: int = 0,
) -> list[Track]:
    result = await _spotify_client.get_saved_tracks(limit=limit, offset=offset)
    return result.items if result.items else []


@mcp.tool()
async def save_tracks(
    uris: list[str],
) -> ActionSuccessResponse:
    await _spotify_client.save_tracks(uris=uris)
    return ActionSuccessResponse(message=f"Saved {len(uris)} track(s) to library")


@mcp.tool()
async def remove_saved_tracks(
    uris: list[str],
) -> ActionSuccessResponse:
    await _spotify_client.remove_saved_tracks(uris=uris)
    return ActionSuccessResponse(message=f"Removed {len(uris)} track(s) from library")


@mcp.tool()
async def is_track_saved(
    uri: str,
) -> dict:
    saved = await _spotify_client.is_track_saved(uri=uri)
    return {"uri": uri, "saved": saved}


@mcp.tool()
async def get_top_tracks(
    time_range: str = "medium_term",
    limit: int = 20,
    offset: int = 0,
) -> list[Track]:
    result = await _spotify_client.get_top_tracks(
        time_range=time_range, limit=limit, offset=offset
    )
    return result.items if result.items else []


@mcp.tool()
async def get_top_artists(
    time_range: str = "medium_term",
    limit: int = 20,
    offset: int = 0,
) -> list[Artist]:
    result = await _spotify_client.get_top_artists(
        time_range=time_range, limit=limit, offset=offset
    )
    return result.items if result.items else []


@mcp.tool()
async def get_artist(
    artist_id: str,
) -> Artist:
    return await _spotify_client.get_artist(artist_id=artist_id)


@mcp.tool()
async def get_artist_top_tracks(
    artist_id: str,
    market: str | None = None,
) -> list[Track]:
    result = await _spotify_client.get_artist_top_tracks(
        artist_id=artist_id, market=market
    )
    return [Track.model_validate(track) for track in result]


@mcp.tool()
async def get_album(
    album_id: str,
) -> AlbumDetails:
    return await _spotify_client.get_album(album_id=album_id)


@mcp.tool()
async def set_repeat(
    state: str,
    device_name: str | None = None,
) -> ActionSuccessResponse:
    device_id = _device_resolver.resolve(device_name)
    await _spotify_client.set_repeat(state=state, device_id=device_id)
    return ActionSuccessResponse(message=f"Repeat mode set to {state}")


@mcp.tool()
async def get_queue() -> QueueResponse:
    return await _spotify_client.queue()


@mcp.tool()
async def seek_track(
    position_ms: int,
    device_name: str | None = None,
) -> ActionSuccessResponse:
    device_id = _device_resolver.resolve(device_name)
    await _spotify_client.seek_track(position_ms=position_ms, device_id=device_id)
    return ActionSuccessResponse(message=f"Seeked to {position_ms}ms")


@mcp.tool()
async def get_saved_shows(
    limit: int = 20,
    offset: int = 0,
) -> list:
    result = await _spotify_client.get_saved_shows(limit=limit, offset=offset)
    return result.items if result.items else []


@mcp.tool()
async def get_saved_albums(
    limit: int = 20,
    offset: int = 0,
) -> SavedAlbumsResponse:
    return await _spotify_client.get_saved_albums(limit=limit, offset=offset)


@mcp.tool()
async def remove_saved_albums(
    album_ids: list[str],
) -> ActionSuccessResponse:
    await _spotify_client.remove_saved_albums(album_ids=album_ids)
    return ActionSuccessResponse(
        message=f"Removed {len(album_ids)} album(s) from library"
    )


@mcp.tool()
async def save_albums(
    album_ids: list[str],
) -> ActionSuccessResponse:
    await _spotify_client.save_albums(album_ids=album_ids)
    return ActionSuccessResponse(message=f"Saved {len(album_ids)} album(s) to library")


@mcp.tool()
async def is_album_saved(
    album_id: str,
) -> dict:
    saved = await _spotify_client.is_album_saved(album_id=album_id)
    return {"album_id": album_id, "saved": saved}


@mcp.tool()
async def get_album_tracks(
    album_id: str,
    limit: int = 50,
    offset: int = 0,
) -> list[Track]:
    result = await _spotify_client.album_tracks(
        album_id=album_id, limit=limit, offset=offset
    )
    return result.items


@mcp.tool()
async def get_playlist(
    playlist_id: str,
) -> Playlist:
    return await _spotify_client.get_playlist(playlist_id=playlist_id)


@mcp.tool()
async def delete_playlist(
    playlist_id: str,
) -> ActionSuccessResponse:
    await _spotify_client.delete_playlist(playlist_id=playlist_id)
    return ActionSuccessResponse(message=f"Playlist {playlist_id} deleted")


@mcp.tool()
async def get_new_releases(
    country: str | None = None,
    limit: int = 20,
    offset: int = 0,
) -> NewReleasesResponse:
    return await _spotify_client.get_new_releases(
        country=country, limit=limit, offset=offset
    )


@mcp.tool()
async def get_currently_playing(
    market: str | None = None,
) -> CurrentlyPlayingResponse | None:
    return await _spotify_client.currently_playing(market=market)
