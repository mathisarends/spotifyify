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
    all_pages: AllOption = False,
    fields: FieldsOption = None,
) -> None:
    async with spotify_client() as spotify:
        result = await fetch_pages(
            spotify.albums.search,
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
async def get_albums(
    album_ids: IdsArgument,
    fields: FieldsOption = None,
) -> None:
    """Fetch one or many albums in a single call."""
    ids = split_values(album_ids)
    market = default_market()
    async with spotify_client() as spotify:
        result = await spotify.albums.get_many(ids, market=market)
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
    offset: OffsetOption = 0,
    all_pages: AllOption = False,
    fields: FieldsOption = None,
) -> None:
    async with spotify_client() as spotify:
        result = await fetch_pages(
            spotify.albums.tracks,
            album_id,
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


@app.command("new-releases")
@async_command
async def new_releases(
    country: Annotated[str | None, typer.Option("--country", "-c")] = None,
    limit: LimitOption = 20,
    offset: OffsetOption = 0,
    all_pages: AllOption = False,
    fields: FieldsOption = None,
) -> None:
    async with spotify_client() as spotify:
        result = await fetch_pages(
            spotify.albums.new_releases,
            country=country,
            limit=limit,
            all_pages=all_pages,
            offset=offset,
        )
    print_result(
        result,
        columns=COLUMNS,
        fields=fields,
    )
