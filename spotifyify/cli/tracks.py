from __future__ import annotations

from typing import Annotated

import typer

from ._core import (
    BATCH_TRACKS,
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
    help="Work with Spotify tracks.",
    rich_markup_mode=None,
    no_args_is_help=True,
)

COLUMNS = ("id", "name", "artists", "album.name", "uri")


@app.command("search")
@async_command
async def search_tracks(
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
    async with spotify_client(scope) as spotify:
        result = await spotify.tracks.find(
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
async def get_tracks(
    track_ids: IdsArgument,
    market: MarketOption = None,
    fmt: FormatOption = None,
    json_output: JsonOption = False,
    raw: RawOption = False,
    fields: FieldsOption = None,
    sort: SortOption = None,
    where: WhereOption = None,
    scope: ScopeOption = None,
) -> None:
    """Fetch one or many tracks in a single call."""
    ids = _split_values(track_ids)
    async with spotify_client(scope) as spotify:
        result = await _gather_batches(
            lambda chunk: spotify.tracks.get_many(chunk, market=market),
            ids,
            BATCH_TRACKS,
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
