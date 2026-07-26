from typing import Annotated

import typer

from .core import (
    BATCH_TRACKS,
    default_market,
    gather_batches,
    split_values,
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
    fields: FieldsOption = None,
) -> None:
    async with spotify_client() as spotify:
        result = await spotify.tracks.find(query, limit=limit, market=default_market())
    print_result(
        result,
        columns=COLUMNS,
        fields=fields,
    )


@app.command("get")
@async_command
async def get_tracks(
    track_ids: IdsArgument,
    fields: FieldsOption = None,
) -> None:
    """Fetch one or many tracks in a single call."""
    ids = split_values(track_ids)
    market = default_market()
    async with spotify_client() as spotify:
        result = await gather_batches(
            lambda chunk: spotify.tracks.get_many(chunk, market=market),
            ids,
            BATCH_TRACKS,
        )
    print_result(
        result,
        columns=COLUMNS,
        fields=fields,
    )
