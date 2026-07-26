from __future__ import annotations

from typing import Annotated

import typer

from .core import (
    BATCH_SHOWS,
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
    help="Work with Spotify shows.",
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
    fields: FieldsOption = None,
) -> None:
    async with spotify_client() as spotify:
        result = await spotify.shows.find(query, limit=limit, market=_default_market())
    print_result(
        result,
        columns=COLUMNS,
        fields=fields,
    )


@app.command("get")
@async_command
async def get_shows(
    show_ids: IdsArgument,
    fields: FieldsOption = None,
) -> None:
    """Fetch one or many shows in a single call."""
    ids = _split_values(show_ids)
    market = _default_market()
    async with spotify_client() as spotify:
        result = await _gather_batches(
            lambda chunk: spotify.shows.get_many(chunk, market=market),
            ids,
            BATCH_SHOWS,
        )
    print_result(
        result,
        columns=COLUMNS,
        fields=fields,
    )


@app.command("episodes")
@async_command
async def show_episodes(
    show_id: Annotated[str, typer.Argument(help="Spotify show ID.")],
    limit: LimitOption = 20,
    fields: FieldsOption = None,
) -> None:
    async with spotify_client() as spotify:
        result = await spotify.shows.episodes(
            show_id, market=_default_market(), limit=limit
        )
    print_result(
        result,
        columns=EPISODE_COLUMNS,
        fields=fields,
    )
