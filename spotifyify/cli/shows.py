from __future__ import annotations

from typing import Annotated

import typer

from ._aliases import AliasGroup
from ._core import BATCH_SHOWS, _coalesce_scopes, _gather_batches, _split_values
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
    help="Work with Spotify shows.",
    cls=AliasGroup,
    rich_markup_mode=None,
    no_args_is_help=True,
)

COLUMNS = ("id", "name", "publisher", "uri")
EPISODE_COLUMNS = ("id", "name", "release_date", "uri")


@app.command("search")
def search_shows(
    query: Annotated[str, typer.Argument(help="Spotify search query.")],
    limit: LimitOption = DEFAULT_LIMIT,
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
        lambda spotify: spotify.shows.find(
            query, limit=limit, offset=offset, market=market
        ),
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
def get_shows(
    show_ids: IdsArgument,
    market: MarketOption = None,
    fmt: FormatOption = None,
    json_output: JsonOption = False,
    raw: RawOption = False,
    fields: FieldsOption = None,
    sort: SortOption = None,
    where: WhereOption = None,
    scope: ScopeOption = None,
) -> None:
    """Fetch one or many shows in a single call."""
    ids = _split_values(show_ids)
    result = _handle(
        lambda spotify: _gather_batches(
            lambda chunk: spotify.shows.get_many(chunk, market=market),
            ids,
            BATCH_SHOWS,
        ),
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


@app.command("episodes")
def show_episodes(
    show_id: Annotated[str, typer.Argument(help="Spotify show ID.")],
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
        lambda spotify: spotify.shows.episodes(
            show_id, market=market, limit=limit, offset=offset
        ),
        scopes=_coalesce_scopes(scope),
    )
    _render(
        result,
        columns=EPISODE_COLUMNS,
        fmt=fmt,
        json_output=json_output,
        raw=raw,
        fields=fields,
        sort=sort,
        where=where,
    )
