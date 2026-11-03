from typing import Annotated

import typer

from spotifyify.cli.core import (
    default_market,
    fetch_pages,
    split_values,
    spotify_client,
)
from spotifyify.cli.options import (
    DEFAULT_LIMIT,
    AllOption,
    FieldsOption,
    IdsArgument,
    LimitOption,
    OffsetOption,
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
    offset: OffsetOption = 0,
    all_pages: AllOption = False,
    fields: FieldsOption = None,
) -> None:
    async with spotify_client() as spotify:
        result = await fetch_pages(
            spotify.shows.search,
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
async def get_shows(
    show_ids: IdsArgument,
    fields: FieldsOption = None,
) -> None:
    """Fetch one or many shows in a single call."""
    ids = split_values(show_ids)
    market = default_market()
    async with spotify_client() as spotify:
        result = await spotify.shows.get_many(ids, market=market)
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
    offset: OffsetOption = 0,
    all_pages: AllOption = False,
    fields: FieldsOption = None,
) -> None:
    async with spotify_client() as spotify:
        result = await fetch_pages(
            spotify.shows.episodes,
            show_id,
            market=default_market(),
            limit=limit,
            all_pages=all_pages,
            offset=offset,
        )
    print_result(
        result,
        columns=EPISODE_COLUMNS,
        fields=fields,
    )
