from __future__ import annotations

from typing import Annotated

import typer

from ._core import (
    BATCH_ALBUMS,
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
    help="Work with Spotify albums.",
    rich_markup_mode=None,
    no_args_is_help=True,
)

COLUMNS = ("id", "name", "artists", "uri")


@app.command("search")
@async_command
async def search_albums(
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
        result = await spotify.albums.find(
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
async def get_albums(
    album_ids: IdsArgument,
    market: MarketOption = None,
    fmt: FormatOption = None,
    json_output: JsonOption = False,
    raw: RawOption = False,
    fields: FieldsOption = None,
    sort: SortOption = None,
    where: WhereOption = None,
    scope: ScopeOption = None,
) -> None:
    """Fetch one or many albums in a single call."""
    ids = _split_values(album_ids)
    async with spotify_client(scope) as spotify:
        result = await _gather_batches(
            lambda chunk: spotify.albums.get_many(chunk, market=market),
            ids,
            BATCH_ALBUMS,
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


@app.command("tracks")
@async_command
async def album_tracks(
    album_id: Annotated[str, typer.Argument(help="Spotify album ID.")],
    limit: LimitOption = 50,
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
        result = await spotify.albums.tracks(
            album_id, limit=limit, offset=offset, market=market
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


@app.command("new-releases")
@async_command
async def new_releases(
    country: Annotated[str | None, typer.Option("--country", "-c")] = None,
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
    async with spotify_client(scope) as spotify:
        result = await spotify.albums.new_releases(
            country=country, limit=limit, offset=offset
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
