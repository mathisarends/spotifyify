from __future__ import annotations

from collections.abc import Awaitable, Callable, Sequence
from typing import Annotated, Any

import typer

from spotifyify import Spotifyify, SpotifyScope

from ._aliases import AliasGroup
from ._core import (
    BATCH_ALBUMS,
    BATCH_EPISODES,
    BATCH_SHOWS,
    BATCH_TRACKS,
    Jsonable,
    _coalesce_scopes,
    _merge_scopes,
    _sequential_batches,
    _split_values,
)
from ._options import (
    FieldsOption,
    FormatOption,
    IdsArgument,
    JsonOption,
    LimitOption,
    MarketOption,
    OffsetOption,
    RawOption,
    ScopeOption,
    SortOption,
    WhereOption,
    _handle,
    _render,
)

app = typer.Typer(
    help="Work with the current user's library.",
    cls=AliasGroup,
    rich_markup_mode=None,
    no_args_is_help=True,
)

SAVED_COLUMNS = ("id", "saved")

READ_SCOPES = [SpotifyScope.USER_LIBRARY_READ.value]
MODIFY_SCOPES = [SpotifyScope.USER_LIBRARY_MODIFY.value]
# Save/remove report the resulting saved state, so they read it back too.
WRITE_SCOPES = _merge_scopes(MODIFY_SCOPES, READ_SCOPES)


def _saved_scope(scope: Sequence[str] | None) -> Sequence[str]:
    return _coalesce_scopes(scope) or READ_SCOPES


def _library_action(
    ids: Sequence[str],
    *,
    action: Callable[[Spotifyify, list[str]], Awaitable[Any]],
    check: Callable[[Spotifyify, list[str]], Awaitable[list[bool]]],
    batch_size: int,
    scope: Sequence[str] | None,
    fmt: str | None,
    json_output: bool,
    raw: bool,
    fields: Sequence[str] | None,
) -> None:
    """Apply a library mutation and report the saved state it produced."""
    item_ids = _split_values(ids)

    async def command(spotify: Spotifyify) -> Jsonable:
        await _sequential_batches(
            lambda chunk: action(spotify, chunk), item_ids, batch_size
        )
        saved = await check(spotify, item_ids)
        return [
            {"id": item_id, "saved": is_saved}
            for item_id, is_saved in zip(item_ids, saved, strict=False)
        ]

    result = _handle(command, scopes=_coalesce_scopes(scope) or WRITE_SCOPES)
    _render(
        result,
        columns=SAVED_COLUMNS,
        fmt=fmt,
        json_output=json_output,
        raw=raw,
        fields=fields,
    )


def _library_check(
    ids: Sequence[str],
    *,
    action: Callable[[Spotifyify, list[str]], Awaitable[list[bool]]],
    scope: Sequence[str] | None,
    fmt: str | None,
    json_output: bool,
    raw: bool,
    fields: Sequence[str] | None,
) -> None:
    item_ids = _split_values(ids)
    result = _handle(
        lambda spotify: action(spotify, item_ids), scopes=_saved_scope(scope)
    )
    payload = [
        {"id": item_id, "saved": saved}
        for item_id, saved in zip(item_ids, result, strict=False)
    ]
    _render(
        payload,
        columns=SAVED_COLUMNS,
        fmt=fmt,
        json_output=json_output,
        raw=raw,
        fields=fields,
    )


@app.command("saved-tracks")
def saved_tracks(
    limit: LimitOption = 20,
    offset: OffsetOption = 0,
    market: MarketOption = None,
    fmt: FormatOption = None,
    json_output: JsonOption = False,
    raw: RawOption = False,
    fields: FieldsOption = None,
    sort: SortOption = None,
    where: WhereOption = None,
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
        columns=("track.id", "track.name", "track.artists", "added_at"),
        fmt=fmt,
        json_output=json_output,
        raw=raw,
        fields=fields,
        sort=sort,
        where=where,
    )


@app.command("saved-albums")
def saved_albums(
    limit: LimitOption = 20,
    offset: OffsetOption = 0,
    market: MarketOption = None,
    fmt: FormatOption = None,
    json_output: JsonOption = False,
    raw: RawOption = False,
    fields: FieldsOption = None,
    sort: SortOption = None,
    where: WhereOption = None,
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
        columns=("album.id", "album.name", "album.artists", "added_at"),
        fmt=fmt,
        json_output=json_output,
        raw=raw,
        fields=fields,
        sort=sort,
        where=where,
    )


@app.command("saved-shows")
def saved_shows(
    limit: LimitOption = 20,
    offset: OffsetOption = 0,
    fmt: FormatOption = None,
    json_output: JsonOption = False,
    raw: RawOption = False,
    fields: FieldsOption = None,
    sort: SortOption = None,
    where: WhereOption = None,
    scope: ScopeOption = None,
) -> None:
    result = _handle(
        lambda spotify: spotify.library.saved_shows(limit=limit, offset=offset),
        scopes=_saved_scope(scope),
    )
    _render(
        result,
        columns=("show.id", "show.name", "show.publisher", "added_at"),
        fmt=fmt,
        json_output=json_output,
        raw=raw,
        fields=fields,
        sort=sort,
        where=where,
    )


@app.command("saved-episodes")
def saved_episodes(
    limit: LimitOption = 20,
    offset: OffsetOption = 0,
    fmt: FormatOption = None,
    json_output: JsonOption = False,
    raw: RawOption = False,
    fields: FieldsOption = None,
    sort: SortOption = None,
    where: WhereOption = None,
    scope: ScopeOption = None,
) -> None:
    result = _handle(
        lambda spotify: spotify.library.saved_episodes(limit=limit, offset=offset),
        scopes=_saved_scope(scope),
    )
    _render(
        result,
        columns=("episode.id", "episode.name", "added_at"),
        fmt=fmt,
        json_output=json_output,
        raw=raw,
        fields=fields,
        sort=sort,
        where=where,
    )


@app.command("top-tracks")
def library_top_tracks(
    time_range: Annotated[str, typer.Option("--time-range")] = "medium_term",
    limit: LimitOption = 20,
    offset: OffsetOption = 0,
    fmt: FormatOption = None,
    json_output: JsonOption = False,
    raw: RawOption = False,
    fields: FieldsOption = None,
    sort: SortOption = None,
    where: WhereOption = None,
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
        columns=("id", "name", "artists", "uri"),
        fmt=fmt,
        json_output=json_output,
        raw=raw,
        fields=fields,
        sort=sort,
        where=where,
    )


@app.command("top-artists")
def library_top_artists(
    time_range: Annotated[str, typer.Option("--time-range")] = "medium_term",
    limit: LimitOption = 20,
    offset: OffsetOption = 0,
    fmt: FormatOption = None,
    json_output: JsonOption = False,
    raw: RawOption = False,
    fields: FieldsOption = None,
    sort: SortOption = None,
    where: WhereOption = None,
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
        columns=("id", "name", "uri"),
        fmt=fmt,
        json_output=json_output,
        raw=raw,
        fields=fields,
        sort=sort,
        where=where,
    )


@app.command("save-tracks")
def save_tracks(
    track_ids: IdsArgument,
    fmt: FormatOption = None,
    json_output: JsonOption = False,
    raw: RawOption = False,
    fields: FieldsOption = None,
    scope: ScopeOption = None,
) -> None:
    _library_action(
        track_ids,
        action=lambda spotify, ids: spotify.library.save_tracks(ids),
        check=lambda spotify, ids: spotify.library.check_tracks(ids),
        batch_size=BATCH_TRACKS,
        scope=scope,
        fmt=fmt,
        json_output=json_output,
        raw=raw,
        fields=fields,
    )


@app.command("remove-tracks")
def remove_tracks(
    track_ids: IdsArgument,
    fmt: FormatOption = None,
    json_output: JsonOption = False,
    raw: RawOption = False,
    fields: FieldsOption = None,
    scope: ScopeOption = None,
) -> None:
    _library_action(
        track_ids,
        action=lambda spotify, ids: spotify.library.remove_tracks(ids),
        check=lambda spotify, ids: spotify.library.check_tracks(ids),
        batch_size=BATCH_TRACKS,
        scope=scope,
        fmt=fmt,
        json_output=json_output,
        raw=raw,
        fields=fields,
    )


@app.command("check-tracks")
def check_tracks(
    track_ids: IdsArgument,
    fmt: FormatOption = None,
    json_output: JsonOption = False,
    raw: RawOption = False,
    fields: FieldsOption = None,
    scope: ScopeOption = None,
) -> None:
    _library_check(
        track_ids,
        action=lambda spotify, ids: spotify.library.check_tracks(ids),
        scope=scope,
        fmt=fmt,
        json_output=json_output,
        raw=raw,
        fields=fields,
    )


@app.command("save-albums")
def save_albums(
    album_ids: IdsArgument,
    fmt: FormatOption = None,
    json_output: JsonOption = False,
    raw: RawOption = False,
    fields: FieldsOption = None,
    scope: ScopeOption = None,
) -> None:
    _library_action(
        album_ids,
        action=lambda spotify, ids: spotify.library.save_albums(ids),
        check=lambda spotify, ids: spotify.library.check_albums(ids),
        batch_size=BATCH_ALBUMS,
        scope=scope,
        fmt=fmt,
        json_output=json_output,
        raw=raw,
        fields=fields,
    )


@app.command("remove-albums")
def remove_albums(
    album_ids: IdsArgument,
    fmt: FormatOption = None,
    json_output: JsonOption = False,
    raw: RawOption = False,
    fields: FieldsOption = None,
    scope: ScopeOption = None,
) -> None:
    _library_action(
        album_ids,
        action=lambda spotify, ids: spotify.library.remove_albums(ids),
        check=lambda spotify, ids: spotify.library.check_albums(ids),
        batch_size=BATCH_ALBUMS,
        scope=scope,
        fmt=fmt,
        json_output=json_output,
        raw=raw,
        fields=fields,
    )


@app.command("check-albums")
def check_albums(
    album_ids: IdsArgument,
    fmt: FormatOption = None,
    json_output: JsonOption = False,
    raw: RawOption = False,
    fields: FieldsOption = None,
    scope: ScopeOption = None,
) -> None:
    _library_check(
        album_ids,
        action=lambda spotify, ids: spotify.library.check_albums(ids),
        scope=scope,
        fmt=fmt,
        json_output=json_output,
        raw=raw,
        fields=fields,
    )


@app.command("save-shows")
def save_shows(
    show_ids: IdsArgument,
    fmt: FormatOption = None,
    json_output: JsonOption = False,
    raw: RawOption = False,
    fields: FieldsOption = None,
    scope: ScopeOption = None,
) -> None:
    _library_action(
        show_ids,
        action=lambda spotify, ids: spotify.library.save_shows(ids),
        check=lambda spotify, ids: spotify.library.check_shows(ids),
        batch_size=BATCH_SHOWS,
        scope=scope,
        fmt=fmt,
        json_output=json_output,
        raw=raw,
        fields=fields,
    )


@app.command("remove-shows")
def remove_shows(
    show_ids: IdsArgument,
    fmt: FormatOption = None,
    json_output: JsonOption = False,
    raw: RawOption = False,
    fields: FieldsOption = None,
    scope: ScopeOption = None,
) -> None:
    _library_action(
        show_ids,
        action=lambda spotify, ids: spotify.library.remove_shows(ids),
        check=lambda spotify, ids: spotify.library.check_shows(ids),
        batch_size=BATCH_SHOWS,
        scope=scope,
        fmt=fmt,
        json_output=json_output,
        raw=raw,
        fields=fields,
    )


@app.command("check-shows")
def check_shows(
    show_ids: IdsArgument,
    fmt: FormatOption = None,
    json_output: JsonOption = False,
    raw: RawOption = False,
    fields: FieldsOption = None,
    scope: ScopeOption = None,
) -> None:
    _library_check(
        show_ids,
        action=lambda spotify, ids: spotify.library.check_shows(ids),
        scope=scope,
        fmt=fmt,
        json_output=json_output,
        raw=raw,
        fields=fields,
    )


@app.command("save-episodes")
def save_episodes(
    episode_ids: IdsArgument,
    fmt: FormatOption = None,
    json_output: JsonOption = False,
    raw: RawOption = False,
    fields: FieldsOption = None,
    scope: ScopeOption = None,
) -> None:
    _library_action(
        episode_ids,
        action=lambda spotify, ids: spotify.library.save_episodes(ids),
        check=lambda spotify, ids: spotify.library.check_episodes(ids),
        batch_size=BATCH_EPISODES,
        scope=scope,
        fmt=fmt,
        json_output=json_output,
        raw=raw,
        fields=fields,
    )


@app.command("remove-episodes")
def remove_episodes(
    episode_ids: IdsArgument,
    fmt: FormatOption = None,
    json_output: JsonOption = False,
    raw: RawOption = False,
    fields: FieldsOption = None,
    scope: ScopeOption = None,
) -> None:
    _library_action(
        episode_ids,
        action=lambda spotify, ids: spotify.library.remove_episodes(ids),
        check=lambda spotify, ids: spotify.library.check_episodes(ids),
        batch_size=BATCH_EPISODES,
        scope=scope,
        fmt=fmt,
        json_output=json_output,
        raw=raw,
        fields=fields,
    )


@app.command("check-episodes")
def check_episodes(
    episode_ids: IdsArgument,
    fmt: FormatOption = None,
    json_output: JsonOption = False,
    raw: RawOption = False,
    fields: FieldsOption = None,
    scope: ScopeOption = None,
) -> None:
    _library_check(
        episode_ids,
        action=lambda spotify, ids: spotify.library.check_episodes(ids),
        scope=scope,
        fmt=fmt,
        json_output=json_output,
        raw=raw,
        fields=fields,
    )
