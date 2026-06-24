from __future__ import annotations

from collections.abc import Awaitable, Callable, Sequence
from typing import Annotated

import typer

from spotifyify import Spotifyify, SpotifyScope

from ._core import (
    Jsonable,
    _coalesce_scopes,
    _print_json,
    _print_success,
    _print_table,
    _split_values,
)
from ._options import (
    FieldsOption,
    IdsArgument,
    JsonOption,
    LimitOption,
    MarketOption,
    OffsetOption,
    ScopeOption,
    _handle,
    _render,
)

app = typer.Typer(help="Work with the current user's library.")


def _saved_scope(scope: Sequence[str] | None) -> Sequence[str]:
    return _coalesce_scopes(scope) or [SpotifyScope.USER_LIBRARY_READ.value]


def _modify_library_scope(scope: Sequence[str] | None) -> Sequence[str]:
    return _coalesce_scopes(scope) or [SpotifyScope.USER_LIBRARY_MODIFY.value]


def _library_action(
    ids: Sequence[str],
    *,
    action: Callable[[Spotifyify, list[str]], Awaitable[Jsonable]],
    scope: Sequence[str] | None,
) -> None:
    _handle(
        lambda spotify: action(spotify, _split_values(ids)),
        scopes=_modify_library_scope(scope),
    )
    _print_success()


def _library_check(
    ids: Sequence[str],
    *,
    action: Callable[[Spotifyify, list[str]], Awaitable[list[bool]]],
    scope: Sequence[str] | None,
    json_output: bool,
) -> None:
    item_ids = _split_values(ids)
    result = _handle(
        lambda spotify: action(spotify, item_ids), scopes=_saved_scope(scope)
    )
    payload = [
        {"id": item_id, "saved": saved}
        for item_id, saved in zip(item_ids, result, strict=False)
    ]
    _print_json(payload) if json_output else _print_table(payload, ("id", "saved"))


@app.command("saved-tracks")
def saved_tracks(
    limit: LimitOption = 20,
    offset: OffsetOption = 0,
    market: MarketOption = None,
    json_output: JsonOption = False,
    fields: FieldsOption = None,
    scope: ScopeOption = None,
) -> None:
    result = _handle(
        lambda spotify: spotify.library.saved_tracks(
            limit=limit, offset=offset, market=market
        ),
        scopes=_saved_scope(scope),
    )
    _render(
        result,
        json_output=json_output,
        fields=fields,
        columns=("track.id", "track.name", "track.artists", "added_at"),
    )


@app.command("saved-albums")
def saved_albums(
    limit: LimitOption = 20,
    offset: OffsetOption = 0,
    market: MarketOption = None,
    json_output: JsonOption = False,
    fields: FieldsOption = None,
    scope: ScopeOption = None,
) -> None:
    result = _handle(
        lambda spotify: spotify.library.saved_albums(
            limit=limit, offset=offset, market=market
        ),
        scopes=_saved_scope(scope),
    )
    _render(
        result,
        json_output=json_output,
        fields=fields,
        columns=("album.id", "album.name", "album.artists", "added_at"),
    )


@app.command("saved-shows")
def saved_shows(
    limit: LimitOption = 20,
    offset: OffsetOption = 0,
    json_output: JsonOption = False,
    fields: FieldsOption = None,
    scope: ScopeOption = None,
) -> None:
    result = _handle(
        lambda spotify: spotify.library.saved_shows(limit=limit, offset=offset),
        scopes=_saved_scope(scope),
    )
    _render(
        result,
        json_output=json_output,
        fields=fields,
        columns=("show.id", "show.name", "show.publisher", "added_at"),
    )


@app.command("saved-episodes")
def saved_episodes(
    limit: LimitOption = 20,
    offset: OffsetOption = 0,
    json_output: JsonOption = False,
    fields: FieldsOption = None,
    scope: ScopeOption = None,
) -> None:
    result = _handle(
        lambda spotify: spotify.library.saved_episodes(limit=limit, offset=offset),
        scopes=_saved_scope(scope),
    )
    _render(
        result,
        json_output=json_output,
        fields=fields,
        columns=("episode.id", "episode.name", "added_at"),
    )


@app.command("top-tracks")
def library_top_tracks(
    time_range: Annotated[str, typer.Option("--time-range")] = "medium_term",
    limit: LimitOption = 20,
    offset: OffsetOption = 0,
    json_output: JsonOption = False,
    fields: FieldsOption = None,
    scope: ScopeOption = None,
) -> None:
    result = _handle(
        lambda spotify: spotify.library.top_tracks(
            time_range=time_range, limit=limit, offset=offset
        ),
        scopes=_coalesce_scopes(scope) or [SpotifyScope.USER_TOP_READ.value],
    )
    _render(
        result,
        json_output=json_output,
        fields=fields,
        columns=("id", "name", "artists", "uri"),
    )


@app.command("top-artists")
def library_top_artists(
    time_range: Annotated[str, typer.Option("--time-range")] = "medium_term",
    limit: LimitOption = 20,
    offset: OffsetOption = 0,
    json_output: JsonOption = False,
    fields: FieldsOption = None,
    scope: ScopeOption = None,
) -> None:
    result = _handle(
        lambda spotify: spotify.library.top_artists(
            time_range=time_range, limit=limit, offset=offset
        ),
        scopes=_coalesce_scopes(scope) or [SpotifyScope.USER_TOP_READ.value],
    )
    _render(
        result,
        json_output=json_output,
        fields=fields,
        columns=("id", "name", "uri"),
    )


@app.command("save-tracks")
def save_tracks(track_ids: IdsArgument, scope: ScopeOption = None) -> None:
    _library_action(
        track_ids,
        action=lambda spotify, ids: spotify.library.save_tracks(ids),
        scope=scope,
    )


@app.command("remove-tracks")
def remove_tracks(track_ids: IdsArgument, scope: ScopeOption = None) -> None:
    _library_action(
        track_ids,
        action=lambda spotify, ids: spotify.library.remove_tracks(ids),
        scope=scope,
    )


@app.command("check-tracks")
def check_tracks(
    track_ids: IdsArgument,
    json_output: JsonOption = False,
    scope: ScopeOption = None,
) -> None:
    _library_check(
        track_ids,
        action=lambda spotify, ids: spotify.library.check_tracks(ids),
        scope=scope,
        json_output=json_output,
    )


@app.command("save-albums")
def save_albums(album_ids: IdsArgument, scope: ScopeOption = None) -> None:
    _library_action(
        album_ids,
        action=lambda spotify, ids: spotify.library.save_albums(ids),
        scope=scope,
    )


@app.command("remove-albums")
def remove_albums(album_ids: IdsArgument, scope: ScopeOption = None) -> None:
    _library_action(
        album_ids,
        action=lambda spotify, ids: spotify.library.remove_albums(ids),
        scope=scope,
    )


@app.command("check-albums")
def check_albums(
    album_ids: IdsArgument,
    json_output: JsonOption = False,
    scope: ScopeOption = None,
) -> None:
    _library_check(
        album_ids,
        action=lambda spotify, ids: spotify.library.check_albums(ids),
        scope=scope,
        json_output=json_output,
    )


@app.command("save-shows")
def save_shows(show_ids: IdsArgument, scope: ScopeOption = None) -> None:
    _library_action(
        show_ids,
        action=lambda spotify, ids: spotify.library.save_shows(ids),
        scope=scope,
    )


@app.command("remove-shows")
def remove_shows(show_ids: IdsArgument, scope: ScopeOption = None) -> None:
    _library_action(
        show_ids,
        action=lambda spotify, ids: spotify.library.remove_shows(ids),
        scope=scope,
    )


@app.command("check-shows")
def check_shows(
    show_ids: IdsArgument,
    json_output: JsonOption = False,
    scope: ScopeOption = None,
) -> None:
    _library_check(
        show_ids,
        action=lambda spotify, ids: spotify.library.check_shows(ids),
        scope=scope,
        json_output=json_output,
    )


@app.command("save-episodes")
def save_episodes(episode_ids: IdsArgument, scope: ScopeOption = None) -> None:
    _library_action(
        episode_ids,
        action=lambda spotify, ids: spotify.library.save_episodes(ids),
        scope=scope,
    )


@app.command("remove-episodes")
def remove_episodes(episode_ids: IdsArgument, scope: ScopeOption = None) -> None:
    _library_action(
        episode_ids,
        action=lambda spotify, ids: spotify.library.remove_episodes(ids),
        scope=scope,
    )


@app.command("check-episodes")
def check_episodes(
    episode_ids: IdsArgument,
    json_output: JsonOption = False,
    scope: ScopeOption = None,
) -> None:
    _library_check(
        episode_ids,
        action=lambda spotify, ids: spotify.library.check_episodes(ids),
        scope=scope,
        json_output=json_output,
    )
