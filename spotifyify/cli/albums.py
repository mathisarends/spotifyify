from __future__ import annotations

from typing import Annotated

import typer

from .core import (
    BATCH_ALBUMS,
    _default_market,
    _gather_batches,
    _split_values,
    spotify_client,
)
from .options import (
    DEFAULT_LIMIT,
    FieldsOption,
    IdsArgument,
    LimitOption,
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
    fields: FieldsOption = None,
) -> None:
    async with spotify_client() as spotify:
        result = await spotify.albums.find(query, limit=limit, market=_default_market())
    print_result(
        result,
        columns=COLUMNS,
        fields=fields,
    )


@app.command("get")
@async_command
async def get_albums(
    album_ids: IdsArgument,
    fields: FieldsOption = None,
) -> None:
    """Fetch one or many albums in a single call."""
    ids = _split_values(album_ids)
    market = _default_market()
    async with spotify_client() as spotify:
        result = await _gather_batches(
            lambda chunk: spotify.albums.get_many(chunk, market=market),
            ids,
            BATCH_ALBUMS,
        )
    print_result(
        result,
        columns=COLUMNS,
        fields=fields,
    )


@app.command("tracks")
@async_command
async def album_tracks(
    album_id: Annotated[str, typer.Argument(help="Spotify album ID.")],
    limit: LimitOption = 50,
    fields: FieldsOption = None,
) -> None:
    async with spotify_client() as spotify:
        result = await spotify.albums.tracks(
            album_id, limit=limit, market=_default_market()
        )
    print_result(
        result,
        columns=COLUMNS,
        fields=fields,
    )


@app.command("new-releases")
@async_command
async def new_releases(
    country: Annotated[str | None, typer.Option("--country", "-c")] = None,
    limit: LimitOption = 20,
    fields: FieldsOption = None,
) -> None:
    async with spotify_client() as spotify:
        result = await spotify.albums.new_releases(country=country, limit=limit)
    print_result(
        result,
        columns=COLUMNS,
        fields=fields,
    )
