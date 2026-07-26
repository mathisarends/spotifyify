from typing import Annotated, Any

import typer

from spotifyify import Spotifyify, SpotifyScope
from spotifyify.exceptions import SpotifyAPIError
from spotifyify.schemas import Device

from .core import (
    PLAYBACK_COLUMNS,
    default_device_id,
    default_market,
    is_raw_output,
    merge_scopes,
    parse_json_object,
    playback_summary,
    settled_playback,
    sort_items,
    split_values,
    is_fresh_track,
    is_paused,
    is_playing,
    plays_uri,
    spotify_client,
)
from .options import (
    FieldsOption,
    LimitOption,
    UrisArgument,
    WaitOption,
    async_command,
    print_result,
)

app = typer.Typer(
    help="Control and inspect Spotify playback.",
    rich_markup_mode=None,
    no_args_is_help=True,
)

READ_SCOPES = [SpotifyScope.USER_READ_PLAYBACK_STATE]
MODIFY_SCOPES = [SpotifyScope.USER_MODIFY_PLAYBACK_STATE]
# Playback mutations report the state they produced, so they need the read
# scope too — otherwise the caller pays a second round trip to learn what
# actually happened.
CONTROL_SCOPES = merge_scopes(MODIFY_SCOPES, READ_SCOPES)


def _select_fallback_device(devices: list[Device]) -> Device | None:
    """Choose a controllable device reproducibly, preferring computers."""
    candidates = [
        device for device in devices if device.id and not device.is_restricted
    ]
    if not candidates:
        return None
    return min(
        candidates,
        key=lambda device: (
            not bool(device.is_active),
            (device.type or "").casefold() != "computer",
            (device.name or "").casefold(),
            device.id or "",
        ),
    )


async def _play_with_device_fallback(
    spotify: Spotifyify,
    *,
    device_id: str | None,
    context_uri: str | None = None,
    uris: list[str] | None = None,
    offset: dict[str, Any] | None = None,
    position_ms: int | None = None,
) -> None:
    """Play normally, discovering a target only when Spotify has no active one."""
    playback = {
        "context_uri": context_uri,
        "uris": uris,
        "offset": offset,
        "position_ms": position_ms,
    }
    try:
        await spotify.player.play(device_id=device_id, **playback)
    except SpotifyAPIError as error:
        if device_id is not None or "no active device" not in error.message.casefold():
            raise

        fallback = _select_fallback_device(await spotify.player.devices())
        if fallback is None:
            raise
        await spotify.player.play(device_id=fallback.id, **playback)


@app.command("state")
@async_command
async def player_state(
    fields: FieldsOption = None,
) -> None:
    async with spotify_client(READ_SCOPES) as spotify:
        state = await spotify.player.state(market=default_market())
    print_result(
        state,
        columns=PLAYBACK_COLUMNS,
        fields=fields,
        project=playback_summary,
    )


@app.command("play")
@async_command
async def player_play(
    context_uri: Annotated[str | None, typer.Option("--context-uri")] = None,
    uri: Annotated[list[str] | None, typer.Option("--uri")] = None,
    offset: Annotated[str | None, typer.Option("--offset-json")] = None,
    position_ms: Annotated[int | None, typer.Option("--position-ms", min=0)] = None,
    wait: WaitOption = True,
    fields: FieldsOption = None,
) -> None:
    uris = split_values(uri) or None
    if uris:
        # Wait for the requested track, not merely for "something is playing".
        until = plays_uri(uris[0])
    elif context_uri:
        until = is_fresh_track
    else:
        until = is_playing
    async with spotify_client(CONTROL_SCOPES) as spotify:
        await _play_with_device_fallback(
            spotify,
            device_id=default_device_id(),
            context_uri=context_uri,
            uris=uris,
            offset=parse_json_object(offset, "--offset-json"),
            position_ms=position_ms,
        )
        state = await settled_playback(spotify, until=until, wait=wait)
    print_result(
        state,
        columns=PLAYBACK_COLUMNS,
        fields=fields,
        project=playback_summary,
    )


@app.command("pause")
@async_command
async def player_pause(
    wait: WaitOption = True,
    fields: FieldsOption = None,
) -> None:
    async with spotify_client(CONTROL_SCOPES) as spotify:
        await spotify.player.pause(device_id=default_device_id())
        state = await settled_playback(spotify, until=is_paused, wait=wait)
    print_result(
        state,
        columns=PLAYBACK_COLUMNS,
        fields=fields,
        project=playback_summary,
    )


@app.command("skip")
@async_command
async def player_skip(
    wait: WaitOption = True,
    fields: FieldsOption = None,
) -> None:
    async with spotify_client(CONTROL_SCOPES) as spotify:
        await spotify.player.skip(device_id=default_device_id())
        state = await settled_playback(spotify, until=is_fresh_track, wait=wait)
    print_result(
        state,
        columns=PLAYBACK_COLUMNS,
        fields=fields,
        project=playback_summary,
    )


@app.command("previous")
@async_command
async def player_previous(
    wait: WaitOption = True,
    fields: FieldsOption = None,
) -> None:
    async with spotify_client(CONTROL_SCOPES) as spotify:
        await spotify.player.previous(device_id=default_device_id())
        state = await settled_playback(spotify, until=is_fresh_track, wait=wait)
    print_result(
        state,
        columns=PLAYBACK_COLUMNS,
        fields=fields,
        project=playback_summary,
    )


@app.command("seek")
@async_command
async def player_seek(
    position_ms: Annotated[int, typer.Argument(min=0)],
    fields: FieldsOption = None,
) -> None:
    async with spotify_client(CONTROL_SCOPES) as spotify:
        await spotify.player.seek(position_ms, device_id=default_device_id())
        state = await settled_playback(spotify)
    print_result(
        state,
        columns=PLAYBACK_COLUMNS,
        fields=fields,
        project=playback_summary,
    )


@app.command("repeat")
@async_command
async def player_repeat(
    state: Annotated[str, typer.Argument(help="track, context, or off")],
    fields: FieldsOption = None,
) -> None:
    async with spotify_client(CONTROL_SCOPES) as spotify:
        await spotify.player.repeat(state, device_id=default_device_id())
        playback = await settled_playback(spotify)
    print_result(
        playback,
        columns=PLAYBACK_COLUMNS,
        fields=fields,
        project=playback_summary,
    )


@app.command("shuffle")
@async_command
async def player_shuffle(
    state: Annotated[bool, typer.Argument()],
    fields: FieldsOption = None,
) -> None:
    async with spotify_client(CONTROL_SCOPES) as spotify:
        await spotify.player.shuffle(state, device_id=default_device_id())
        playback = await settled_playback(spotify)
    print_result(
        playback,
        columns=PLAYBACK_COLUMNS,
        fields=fields,
        project=playback_summary,
    )


@app.command("volume")
@async_command
async def player_volume(
    volume_percent: Annotated[int, typer.Argument(min=0, max=100)],
    fields: FieldsOption = None,
) -> None:
    async with spotify_client(CONTROL_SCOPES) as spotify:
        await spotify.player.volume(volume_percent, device_id=default_device_id())
        state = await settled_playback(spotify)
    print_result(
        state,
        columns=PLAYBACK_COLUMNS,
        fields=fields,
        project=playback_summary,
    )


@app.command("queue")
@async_command
async def player_queue(
    fields: FieldsOption = None,
) -> None:
    async with spotify_client(READ_SCOPES) as spotify:
        result = await spotify.player.queue()
    print_result(
        result,
        columns=("id", "name", "artists", "uri"),
        fields=fields,
    )


@app.command("add-to-queue")
@async_command
async def add_to_queue(
    uris: UrisArgument,
    fields: FieldsOption = None,
) -> None:
    """Queue one or many tracks or episodes in a single call."""
    queued = split_values(uris)
    device_id = default_device_id()

    async with spotify_client(CONTROL_SCOPES) as spotify:
        # Spotify has no bulk queue endpoint and the queue is ordered, so these
        # must stay sequential.
        for uri in queued:
            await spotify.player.add_to_queue(uri, device_id=device_id)
        state = await settled_playback(spotify)
    print_result(
        state,
        columns=PLAYBACK_COLUMNS,
        fields=fields,
        project=playback_summary,
    )


@app.command("transfer")
@async_command
async def transfer_playback(
    device_id: Annotated[str, typer.Argument(help="Spotify device ID.")],
    play: Annotated[bool, typer.Option("--play/--no-play")] = False,
    wait: WaitOption = True,
    fields: FieldsOption = None,
) -> None:
    async with spotify_client(CONTROL_SCOPES) as spotify:
        await spotify.player.transfer(device_id, play=play)
        state = await settled_playback(
            spotify,
            until=is_playing if play else None,
            wait=wait,
        )
    print_result(
        state,
        columns=PLAYBACK_COLUMNS,
        fields=fields,
        project=playback_summary,
    )


@app.command("devices")
@async_command
async def player_devices(
    fields: FieldsOption = None,
) -> None:
    async with spotify_client(READ_SCOPES) as spotify:
        result = await spotify.player.devices()
    # Spotify returns devices in no defined order; sort so repeated calls and
    # any caching built on top of them stay reproducible.
    display_result = result if is_raw_output() else sort_items(result or [], ("id",))
    print_result(
        display_result,
        columns=("id", "name", "type", "is_active", "volume_percent"),
        fields=fields,
    )


@app.command("recently-played")
@async_command
async def recently_played(
    limit: LimitOption = 20,
    after: Annotated[int | None, typer.Option("--after")] = None,
    before: Annotated[int | None, typer.Option("--before")] = None,
    fields: FieldsOption = None,
) -> None:
    async with spotify_client([SpotifyScope.USER_READ_RECENTLY_PLAYED]) as spotify:
        result = await spotify.player.recently_played(
            limit=limit, after=after, before=before
        )
    print_result(
        result,
        columns=("track.id", "track.name", "track.artists", "played_at"),
        fields=fields,
    )
