from __future__ import annotations

from typing import Annotated

import typer

from ._aliases import AliasGroup
from ._core import BATCH_ARTISTS, _coalesce_scopes, _gather_batches, _split_values
from ._options import (
    DEFAULT_LIMIT,
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
    help="Work with Spotify artists.",
    cls=AliasGroup,
    rich_markup_mode=None,
    no_args_is_help=True,
)

COLUMNS = ("id", "name", "uri")
TRACK_COLUMNS = ("id", "name", "artists", "uri")
ALBUM_COLUMNS = ("id", "name", "album_type", "uri")


@app.command("search")
def search_artists(
    query: Annotated[str, typer.Argument(help="Spotify search query.")],
    limit: LimitOption = DEFAULT_LIMIT,
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
        lambda spotify: spotify.artists.find(query, limit=limit, offset=offset),
        scopes=_coalesce_scopes(scope),
    )
    _render(
        result,
        columns=COLUMNS,
        fmt=fmt,
        json_output=json_output,
        raw=raw,
        fields=fields,
        sort=sort,
        where=where,
    )


@app.command("get")
def get_artists(
    artist_ids: IdsArgument,
    fmt: FormatOption = None,
    json_output: JsonOption = False,
    raw: RawOption = False,
    fields: FieldsOption = None,
    sort: SortOption = None,
    where: WhereOption = None,
    scope: ScopeOption = None,
) -> None:
    """Fetch one or many artists in a single call."""
    ids = _split_values(artist_ids)
    result = _handle(
        lambda spotify: _gather_batches(spotify.artists.get_many, ids, BATCH_ARTISTS),
        scopes=_coalesce_scopes(scope),
    )
    _render(
        result,
        columns=COLUMNS,
        fmt=fmt,
        json_output=json_output,
        raw=raw,
        fields=fields,
        sort=sort,
        where=where,
    )


@app.command("top-tracks")
def artist_top_tracks(
    artist_id: Annotated[str, typer.Argument(help="Spotify artist ID.")],
    market: Annotated[str, typer.Option("--market", "-m")] = "US",
    fmt: FormatOption = None,
    json_output: JsonOption = False,
    raw: RawOption = False,
    fields: FieldsOption = None,
    sort: SortOption = None,
    where: WhereOption = None,
    scope: ScopeOption = None,
) -> None:
    result = _handle(
        lambda spotify: spotify.artists.top_tracks(artist_id, market=market),
        scopes=_coalesce_scopes(scope),
    )
    _render(
        result,
        columns=TRACK_COLUMNS,
        fmt=fmt,
        json_output=json_output,
        raw=raw,
        fields=fields,
        sort=sort,
        where=where,
    )


@app.command("albums")
def artist_albums(
    artist_id: Annotated[str, typer.Argument(help="Spotify artist ID.")],
    include_groups: Annotated[
        str | None,
        typer.Option("--include-groups", help="album,single,appears_on,compilation"),
    ] = None,
    market: MarketOption = None,
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
        lambda spotify: spotify.artists.albums(
            artist_id,
            include_groups=include_groups,
            market=market,
            limit=limit,
            offset=offset,
        ),
        scopes=_coalesce_scopes(scope),
    )
    _render(
        result,
        columns=ALBUM_COLUMNS,
        fmt=fmt,
        json_output=json_output,
        raw=raw,
        fields=fields,
        sort=sort,
        where=where,
    )


@app.command("related")
def related_artists(
    artist_id: Annotated[str, typer.Argument(help="Spotify artist ID.")],
    fmt: FormatOption = None,
    json_output: JsonOption = False,
    raw: RawOption = False,
    fields: FieldsOption = None,
    sort: SortOption = None,
    where: WhereOption = None,
    scope: ScopeOption = None,
) -> None:
    result = _handle(
        lambda spotify: spotify.artists.related(artist_id),
        scopes=_coalesce_scopes(scope),
    )
    _render(
        result,
        columns=COLUMNS,
        fmt=fmt,
        json_output=json_output,
        raw=raw,
        fields=fields,
        sort=sort,
        where=where,
    )
