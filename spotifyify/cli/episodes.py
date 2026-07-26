from __future__ import annotations

from typing import Annotated

import typer

from ._aliases import AliasGroup
from ._core import (
    BATCH_EPISODES,
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
    help="Work with Spotify episodes.",
    cls=AliasGroup,
    rich_markup_mode=None,
    no_args_is_help=True,
)

SEARCH_COLUMNS = ("id", "name", "release_date", "uri")
COLUMNS = ("id", "name", "show.name", "uri")


@app.command("search")
@async_command
async def search_episodes(
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
        result = await spotify.episodes.find(
            query, limit=limit, offset=offset, market=market
        )
    print_result(
        result,
        columns=SEARCH_COLUMNS,
        fmt=fmt,
        json_output=json_output,
        raw=raw,
        fields=fields,
        sort=sort,
        where=where,
    )


@app.command("get")
@async_command
async def get_episodes(
    episode_ids: IdsArgument,
    market: MarketOption = None,
    fmt: FormatOption = None,
    json_output: JsonOption = False,
    raw: RawOption = False,
    fields: FieldsOption = None,
    sort: SortOption = None,
    where: WhereOption = None,
    scope: ScopeOption = None,
) -> None:
    """Fetch one or many episodes in a single call."""
    ids = _split_values(episode_ids)
    async with spotify_client(_coalesce_scopes(scope)) as spotify:
        result = await _gather_batches(
            lambda chunk: spotify.episodes.get_many(chunk, market=market),
            ids,
            BATCH_EPISODES,
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
