from __future__ import annotations

from typing import Annotated, Any

import typer

from spotifyify import Spotifyify, SpotifyScope
from spotifyify.exceptions import SpotifyAPIError
from spotifyify.schemas import Device

from ._aliases import AliasGroup
from ._core import (
    PLAYBACK_COLUMNS,
    Predicate,
    _coalesce_scopes,
    _merge_scopes,
    _parse_json_object,
    _playback_summary,
    _settled_playback,
    _sort_items,
    _split_values,
    is_fresh_track,
    is_paused,
    is_playing,
    plays_uri,
)
from ._options import (
    DeviceOption,
    FieldsOption,
    FormatOption,
    JsonOption,
    LimitOption,
    RawOption,
    ScopeOption,
    SortOption,
    UrisArgument,
    WaitOption,
    WhereOption,
    _handle,
    _render,
)

app = typer.Typer(
    help="Control and inspect Spotify playback.",
    cls=AliasGroup,
    rich_markup_mode=None,
    no_args_is_help=True,
)

READ_SCOPES = [SpotifyScope.USER_READ_PLAYBACK_STATE.value]
MODIFY_SCOPES = [SpotifyScope.USER_MODIFY_PLAYBACK_STATE.value]
# Playback mutations report the state they produced, so they need the read
# scope too — otherwise the caller pays a second round trip to learn what
# actually happened.
CONTROL_SCOPES = _merge_scopes(MODIFY_SCOPES, READ_SCOPES)


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


def _control(
    action,
    *,
    scope,
    until: Predicate | None = None,
    wait: bool = True,
    fmt: str | None,
    json_output: bool,
    raw: bool,
    fields,
) -> None:
    """Run a playback mutation and print the state it produced."""

    async def command(spotify: Spotifyify) -> Any:
        await action(spotify)
        return await _settled_playback(spotify, until=until, wait=wait)

    result = _handle(command, scopes=_coalesce_scopes(scope) or CONTROL_SCOPES)
    _render(
        result,
        columns=PLAYBACK_COLUMNS,
        fmt=fmt,
        json_output=json_output,
        raw=raw,
        fields=fields,
    )


@app.command("state")
def player_state(
    market: Annotated[
        str | None,
        typer.Option("--market", "-m", help="ISO 3166-1 alpha-2 market code."),
    ] = None,
    fmt: FormatOption = None,
    json_output: JsonOption = False,
    raw: RawOption = False,
    fields: FieldsOption = None,
    scope: ScopeOption = None,
) -> None:
    result = _handle(
        lambda spotify: spotify.player.state(market=market),
        scopes=_coalesce_scopes(scope) or READ_SCOPES,
    )
    _render(
        _playback_summary(result),
        columns=PLAYBACK_COLUMNS,
        fmt=fmt,
        json_output=json_output,
        raw=raw,
        fields=fields,
    )


@app.command("play")
def player_play(
    device_id: DeviceOption = None,
    context_uri: Annotated[str | None, typer.Option("--context-uri")] = None,
    uri: Annotated[list[str] | None, typer.Option("--uri")] = None,
    offset: Annotated[str | None, typer.Option("--offset-json")] = None,
    position_ms: Annotated[int | None, typer.Option("--position-ms", min=0)] = None,
    wait: WaitOption = True,
    fmt: FormatOption = None,
    json_output: JsonOption = False,
    raw: RawOption = False,
    fields: FieldsOption = None,
    scope: ScopeOption = None,
) -> None:
    uris = _split_values(uri) or None
    if uris:
        # Wait for the requested track, not merely for "something is playing".
        until = plays_uri(uris[0])
    elif context_uri:
        until = is_fresh_track
    else:
        until = is_playing
    _control(
        lambda spotify: _play_with_device_fallback(
            spotify,
            device_id=device_id,
            context_uri=context_uri,
            uris=uris,
            offset=_parse_json_object(offset, "--offset-json"),
            position_ms=position_ms,
        ),
        scope=scope,
        until=until,
        wait=wait,
        fmt=fmt,
        json_output=json_output,
        raw=raw,
        fields=fields,
    )


@app.command("pause")
def player_pause(
    device_id: DeviceOption = None,
    wait: WaitOption = True,
    fmt: FormatOption = None,
    json_output: JsonOption = False,
    raw: RawOption = False,
    fields: FieldsOption = None,
    scope: ScopeOption = None,
) -> None:
    _control(
        lambda spotify: spotify.player.pause(device_id=device_id),
        scope=scope,
        until=is_paused,
        wait=wait,
        fmt=fmt,
        json_output=json_output,
        raw=raw,
        fields=fields,
    )


@app.command("skip")
def player_skip(
    device_id: DeviceOption = None,
    wait: WaitOption = True,
    fmt: FormatOption = None,
    json_output: JsonOption = False,
    raw: RawOption = False,
    fields: FieldsOption = None,
    scope: ScopeOption = None,
) -> None:
    _control(
        lambda spotify: spotify.player.skip(device_id=device_id),
        scope=scope,
        until=is_fresh_track,
        wait=wait,
        fmt=fmt,
        json_output=json_output,
        raw=raw,
        fields=fields,
    )


@app.command("previous")
def player_previous(
    device_id: DeviceOption = None,
    wait: WaitOption = True,
    fmt: FormatOption = None,
    json_output: JsonOption = False,
    raw: RawOption = False,
    fields: FieldsOption = None,
    scope: ScopeOption = None,
) -> None:
    _control(
        lambda spotify: spotify.player.previous(device_id=device_id),
        scope=scope,
        until=is_fresh_track,
        wait=wait,
        fmt=fmt,
        json_output=json_output,
        raw=raw,
        fields=fields,
    )


@app.command("seek")
def player_seek(
    position_ms: Annotated[int, typer.Argument(min=0)],
    device_id: DeviceOption = None,
    fmt: FormatOption = None,
    json_output: JsonOption = False,
    raw: RawOption = False,
    fields: FieldsOption = None,
    scope: ScopeOption = None,
) -> None:
    _control(
        lambda spotify: spotify.player.seek(position_ms, device_id=device_id),
        scope=scope,
        fmt=fmt,
        json_output=json_output,
        raw=raw,
        fields=fields,
    )


@app.command("repeat")
def player_repeat(
    state: Annotated[str, typer.Argument(help="track, context, or off")],
    device_id: DeviceOption = None,
    fmt: FormatOption = None,
    json_output: JsonOption = False,
    raw: RawOption = False,
    fields: FieldsOption = None,
    scope: ScopeOption = None,
) -> None:
    _control(
        lambda spotify: spotify.player.repeat(state, device_id=device_id),
        scope=scope,
        fmt=fmt,
        json_output=json_output,
        raw=raw,
        fields=fields,
    )


@app.command("shuffle")
def player_shuffle(
    state: Annotated[bool, typer.Argument()],
    device_id: DeviceOption = None,
    fmt: FormatOption = None,
    json_output: JsonOption = False,
    raw: RawOption = False,
    fields: FieldsOption = None,
    scope: ScopeOption = None,
) -> None:
    _control(
        lambda spotify: spotify.player.shuffle(state, device_id=device_id),
        scope=scope,
        fmt=fmt,
        json_output=json_output,
        raw=raw,
        fields=fields,
    )


@app.command("volume")
def player_volume(
    volume_percent: Annotated[int, typer.Argument(min=0, max=100)],
    device_id: DeviceOption = None,
    fmt: FormatOption = None,
    json_output: JsonOption = False,
    raw: RawOption = False,
    fields: FieldsOption = None,
    scope: ScopeOption = None,
) -> None:
    _control(
        lambda spotify: spotify.player.volume(volume_percent, device_id=device_id),
        scope=scope,
        fmt=fmt,
        json_output=json_output,
        raw=raw,
        fields=fields,
    )


@app.command("queue")
def player_queue(
    fmt: FormatOption = None,
    json_output: JsonOption = False,
    raw: RawOption = False,
    fields: FieldsOption = None,
    sort: SortOption = None,
    where: WhereOption = None,
    scope: ScopeOption = None,
) -> None:
    result = _handle(
        lambda spotify: spotify.player.queue(),
        scopes=_coalesce_scopes(scope) or READ_SCOPES,
    )
    _render(
        result,
        columns=("id", "name", "artists", "uri"),
        fmt=fmt,
        json_output=json_output,
        raw=raw,
        fields=fields,
        sort=sort,
        where=where,
    )


@app.command("add-to-queue")
def add_to_queue(
    uris: UrisArgument,
    device_id: DeviceOption = None,
    fmt: FormatOption = None,
    json_output: JsonOption = False,
    raw: RawOption = False,
    fields: FieldsOption = None,
    scope: ScopeOption = None,
) -> None:
    """Queue one or many tracks or episodes in a single call."""
    queued = _split_values(uris)

    async def enqueue(spotify: Spotifyify) -> None:
        # Spotify has no bulk queue endpoint and the queue is ordered, so these
        # must stay sequential.
        for uri in queued:
            await spotify.player.add_to_queue(uri, device_id=device_id)

    _control(
        enqueue,
        scope=scope,
        fmt=fmt,
        json_output=json_output,
        raw=raw,
        fields=fields,
    )


@app.command("transfer")
def transfer_playback(
    device_id: Annotated[str, typer.Argument(help="Spotify device ID.")],
    play: Annotated[bool, typer.Option("--play/--no-play")] = False,
    wait: WaitOption = True,
    fmt: FormatOption = None,
    json_output: JsonOption = False,
    raw: RawOption = False,
    fields: FieldsOption = None,
    scope: ScopeOption = None,
) -> None:
    _control(
        lambda spotify: spotify.player.transfer(device_id, play=play),
        scope=scope,
        until=is_playing if play else None,
        wait=wait,
        fmt=fmt,
        json_output=json_output,
        raw=raw,
        fields=fields,
    )


@app.command("devices")
def player_devices(
    fmt: FormatOption = None,
    json_output: JsonOption = False,
    raw: RawOption = False,
    fields: FieldsOption = None,
    sort: SortOption = None,
    where: WhereOption = None,
    scope: ScopeOption = None,
) -> None:
    result = _handle(
        lambda spotify: spotify.player.devices(),
        scopes=_coalesce_scopes(scope) or READ_SCOPES,
    )
    # Spotify returns devices in no defined order; sort so repeated calls and
    # any caching built on top of them stay reproducible.
    _render(
        _sort_items(result or [], ("id",)),
        columns=("id", "name", "type", "is_active", "volume_percent"),
        fmt=fmt,
        json_output=json_output,
        raw=raw,
        fields=fields,
        sort=sort,
        where=where,
    )


@app.command("recently-played")
def recently_played(
    limit: LimitOption = 20,
    after: Annotated[int | None, typer.Option("--after")] = None,
    before: Annotated[int | None, typer.Option("--before")] = None,
    fmt: FormatOption = None,
    json_output: JsonOption = False,
    raw: RawOption = False,
    fields: FieldsOption = None,
    sort: SortOption = None,
    where: WhereOption = None,
    scope: ScopeOption = None,
) -> None:
    result = _handle(
        lambda spotify: spotify.player.recently_played(
            limit=limit, after=after, before=before
        ),
        scopes=_coalesce_scopes(scope)
        or [SpotifyScope.USER_READ_RECENTLY_PLAYED.value],
    )
    _render(
        result,
        columns=("track.id", "track.name", "track.artists", "played_at"),
        fmt=fmt,
        json_output=json_output,
        raw=raw,
        fields=fields,
        sort=sort,
        where=where,
    )
