from __future__ import annotations

from typing import Annotated

import typer

from .core import (
    BATCH_EPISODES,
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
    help="Work with Spotify episodes.",
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
    fields: FieldsOption = None,
) -> None:
    async with spotify_client() as spotify:
        result = await spotify.episodes.find(
            query, limit=limit, market=_default_market()
        )
    print_result(
        result,
        columns=SEARCH_COLUMNS,
        fields=fields,
    )


@app.command("get")
@async_command
async def get_episodes(
    episode_ids: IdsArgument,
    fields: FieldsOption = None,
) -> None:
    """Fetch one or many episodes in a single call."""
    ids = _split_values(episode_ids)
    market = _default_market()
    async with spotify_client() as spotify:
        result = await _gather_batches(
            lambda chunk: spotify.episodes.get_many(chunk, market=market),
            ids,
            BATCH_EPISODES,
        )
    print_result(
        result,
        columns=COLUMNS,
        fields=fields,
    )
