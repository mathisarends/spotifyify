from spotifyify.cli.core import fetch_pages
from spotifyify.cli.options import OffsetOption, AllOption
from typing import Annotated

import typer

from spotifyify.cli.core import (
    default_market,
    split_values,
    spotify_client,
)
from spotifyify.cli.options import (
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
    offset: OffsetOption = 0,
    all_pages: AllOption = False,
    fields: FieldsOption = None,
) -> None:
    async with spotify_client() as spotify:
        result = await fetch_pages(
            spotify.tracks.search,
            query,
            limit=limit,
            market=default_market(),
            all_pages=all_pages,
            offset=offset,
        )
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
        result = await spotify.tracks.get_many(ids, market=market)
    print_result(
        result,
        columns=COLUMNS,
        fields=fields,
    )
