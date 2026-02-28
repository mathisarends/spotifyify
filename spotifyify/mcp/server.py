from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from mcp.server.fastmcp import FastMCP

from spotifyify import AsyncSpotify, SpotifyScope
from spotifyify.credentials import SpotifyCredentials
from spotifyify.device_resolver import DeviceResolver
from spotifyify.schemas import (
    DevicesResponse,
    PlaybackState,
    RecentlyPlayedResponse,
    SimplifiedAlbum,
    Track,
)
from spotifyify.types import ActionSuccessResponse

_SPOTIFY_SCOPES = [
    SpotifyScope.USER_READ_PLAYBACK_STATE,
    SpotifyScope.USER_MODIFY_PLAYBACK_STATE,
    SpotifyScope.USER_LIBRARY_READ,
    SpotifyScope.USER_LIBRARY_MODIFY,
    SpotifyScope.USER_TOP_READ,
    SpotifyScope.USER_READ_RECENTLY_PLAYED,
    SpotifyScope.PLAYLIST_MODIFY_PUBLIC,
    SpotifyScope.PLAYLIST_MODIFY_PRIVATE,
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


@mcp.tool()
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


@mcp.tool()
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
