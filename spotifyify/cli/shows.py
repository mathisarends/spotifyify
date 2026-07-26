from __future__ import annotations

from typing import Annotated

import typer

from ._aliases import AliasGroup
from ._core import (
    BATCH_SHOWS,
    _coalesce_scopes,
    _gather_batches,
    _split_values,
    spotify_client,
)
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
    async_command,
    print_result,
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
@async_command
async def search_shows(
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
    async with spotify_client(_coalesce_scopes(scope)) as spotify:
        result = await spotify.shows.find(
            query, limit=limit, offset=offset, market=market
        )
    print_result(
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
@async_command
async def get_shows(
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
    async with spotify_client(_coalesce_scopes(scope)) as spotify:
        result = await _gather_batches(
            lambda chunk: spotify.shows.get_many(chunk, market=market),
            ids,
            BATCH_SHOWS,
        )
    print_result(
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
@async_command
async def show_episodes(
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
    async with spotify_client(_coalesce_scopes(scope)) as spotify:
        result = await spotify.shows.episodes(
            show_id, market=market, limit=limit, offset=offset
        )
    print_result(
        result,
        columns=EPISODE_COLUMNS,
        fmt=fmt,
        json_output=json_output,
        raw=raw,
        fields=fields,
        sort=sort,
        where=where,
    )
