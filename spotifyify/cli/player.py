from __future__ import annotations

from typing import Annotated

import typer

from spotifyify import SpotifyScope

from ._core import _coalesce_scopes, _parse_json_object, _print_success, _split_values
from ._options import (
    DeviceOption,
    FieldsOption,
    JsonOption,
    LimitOption,
    ScopeOption,
    _handle,
    _render,
)

app = typer.Typer(help="Control and inspect Spotify playback.")


@app.command("state")
def player_state(
    market: Annotated[
        str | None,
        typer.Option("--market", "-m", help="ISO 3166-1 alpha-2 market code."),
    ] = None,
    json_output: JsonOption = False,
    fields: FieldsOption = None,
    scope: ScopeOption = None,
) -> None:
    result = _handle(
        lambda spotify: spotify.player.state(market=market),
        scopes=_coalesce_scopes(scope) or [SpotifyScope.USER_READ_PLAYBACK_STATE.value],
    )
    _render(
        result,
        json_output=json_output,
        fields=fields,
        columns=("item.id", "item.name", "is_playing", "progress_ms"),
    )


@app.command("play")
def player_play(
    device_id: DeviceOption = None,
    context_uri: Annotated[str | None, typer.Option("--context-uri")] = None,
    uri: Annotated[list[str] | None, typer.Option("--uri")] = None,
    offset: Annotated[str | None, typer.Option("--offset-json")] = None,
    position_ms: Annotated[int | None, typer.Option("--position-ms", min=0)] = None,
    scope: ScopeOption = None,
) -> None:
    _handle(
        lambda spotify: spotify.player.play(
            device_id=device_id,
            context_uri=context_uri,
            uris=_split_values(uri) or None,
            offset=_parse_json_object(offset, "--offset-json"),
            position_ms=position_ms,
        ),
        scopes=_coalesce_scopes(scope)
        or [SpotifyScope.USER_MODIFY_PLAYBACK_STATE.value],
    )
    _print_success()


@app.command("pause")
def player_pause(device_id: DeviceOption = None, scope: ScopeOption = None) -> None:
    _handle(
        lambda spotify: spotify.player.pause(device_id=device_id),
        scopes=_coalesce_scopes(scope)
        or [SpotifyScope.USER_MODIFY_PLAYBACK_STATE.value],
    )
    _print_success()


@app.command("skip")
def player_skip(device_id: DeviceOption = None, scope: ScopeOption = None) -> None:
    _handle(
        lambda spotify: spotify.player.skip(device_id=device_id),
        scopes=_coalesce_scopes(scope)
        or [SpotifyScope.USER_MODIFY_PLAYBACK_STATE.value],
    )
    _print_success()


@app.command("previous")
def player_previous(device_id: DeviceOption = None, scope: ScopeOption = None) -> None:
    _handle(
        lambda spotify: spotify.player.previous(device_id=device_id),
        scopes=_coalesce_scopes(scope)
        or [SpotifyScope.USER_MODIFY_PLAYBACK_STATE.value],
    )
    _print_success()


@app.command("seek")
def player_seek(
    position_ms: Annotated[int, typer.Argument(min=0)],
    device_id: DeviceOption = None,
    scope: ScopeOption = None,
) -> None:
    _handle(
        lambda spotify: spotify.player.seek(position_ms, device_id=device_id),
        scopes=_coalesce_scopes(scope)
        or [SpotifyScope.USER_MODIFY_PLAYBACK_STATE.value],
    )
    _print_success()


@app.command("repeat")
def player_repeat(
    state: Annotated[str, typer.Argument(help="track, context, or off")],
    device_id: DeviceOption = None,
    scope: ScopeOption = None,
) -> None:
    _handle(
        lambda spotify: spotify.player.repeat(state, device_id=device_id),
        scopes=_coalesce_scopes(scope)
        or [SpotifyScope.USER_MODIFY_PLAYBACK_STATE.value],
    )
    _print_success()


@app.command("shuffle")
def player_shuffle(
    state: Annotated[bool, typer.Argument()],
    device_id: DeviceOption = None,
    scope: ScopeOption = None,
) -> None:
    _handle(
        lambda spotify: spotify.player.shuffle(state, device_id=device_id),
        scopes=_coalesce_scopes(scope)
        or [SpotifyScope.USER_MODIFY_PLAYBACK_STATE.value],
    )
    _print_success()


@app.command("volume")
def player_volume(
    volume_percent: Annotated[int, typer.Argument(min=0, max=100)],
    device_id: DeviceOption = None,
    scope: ScopeOption = None,
) -> None:
    _handle(
        lambda spotify: spotify.player.volume(volume_percent, device_id=device_id),
        scopes=_coalesce_scopes(scope)
        or [SpotifyScope.USER_MODIFY_PLAYBACK_STATE.value],
    )
    _print_success()


@app.command("queue")
def player_queue(
    json_output: JsonOption = False,
    fields: FieldsOption = None,
    scope: ScopeOption = None,
) -> None:
    result = _handle(
        lambda spotify: spotify.player.queue(),
        scopes=_coalesce_scopes(scope) or [SpotifyScope.USER_READ_PLAYBACK_STATE.value],
    )
    _render(
        result,
        json_output=json_output,
        fields=fields,
        columns=("id", "name", "artists", "uri"),
    )


@app.command("add-to-queue")
def add_to_queue(
    uri: Annotated[str, typer.Argument(help="Track or episode URI.")],
    device_id: DeviceOption = None,
    scope: ScopeOption = None,
) -> None:
    _handle(
        lambda spotify: spotify.player.add_to_queue(uri, device_id=device_id),
        scopes=_coalesce_scopes(scope)
        or [SpotifyScope.USER_MODIFY_PLAYBACK_STATE.value],
    )
    _print_success()


@app.command("transfer")
def transfer_playback(
    device_id: Annotated[str, typer.Argument(help="Spotify device ID.")],
    play: Annotated[bool, typer.Option("--play/--no-play")] = False,
    scope: ScopeOption = None,
) -> None:
    _handle(
        lambda spotify: spotify.player.transfer(device_id, play=play),
        scopes=_coalesce_scopes(scope)
        or [SpotifyScope.USER_MODIFY_PLAYBACK_STATE.value],
    )
    _print_success()


@app.command("devices")
def player_devices(
    json_output: JsonOption = False,
    fields: FieldsOption = None,
    scope: ScopeOption = None,
) -> None:
    result = _handle(
        lambda spotify: spotify.player.devices(),
        scopes=_coalesce_scopes(scope) or [SpotifyScope.USER_READ_PLAYBACK_STATE.value],
    )
    _render(
        result,
        json_output=json_output,
        fields=fields,
        columns=("id", "name", "type", "is_active", "volume_percent"),
    )


@app.command("recently-played")
def recently_played(
    limit: LimitOption = 20,
    after: Annotated[int | None, typer.Option("--after")] = None,
    before: Annotated[int | None, typer.Option("--before")] = None,
    json_output: JsonOption = False,
    fields: FieldsOption = None,
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
        json_output=json_output,
        fields=fields,
        columns=("track.id", "track.name", "played_at"),
    )
