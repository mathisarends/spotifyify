from typing import Annotated

import typer

from .core import (
    BATCH_ARTISTS,
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
    help="Work with Spotify artists.",
    rich_markup_mode=None,
    no_args_is_help=True,
)

COLUMNS = ("id", "name", "uri")
TRACK_COLUMNS = ("id", "name", "artists", "uri")
ALBUM_COLUMNS = ("id", "name", "album_type", "uri")


@app.command("search")
@async_command
async def search_artists(
    query: Annotated[str, typer.Argument(help="Spotify search query.")],
    limit: LimitOption = DEFAULT_LIMIT,
    fields: FieldsOption = None,
) -> None:
    async with spotify_client() as spotify:
        result = await spotify.artists.find(query, limit=limit)
    print_result(
        result,
        columns=COLUMNS,
        fields=fields,
    )


@app.command("get")
@async_command
async def get_artists(
    artist_ids: IdsArgument,
    fields: FieldsOption = None,
) -> None:
    """Fetch one or many artists in a single call."""
    ids = split_values(artist_ids)
    async with spotify_client() as spotify:
        result = await gather_batches(spotify.artists.get_many, ids, BATCH_ARTISTS)
    print_result(
        result,
        columns=COLUMNS,
        fields=fields,
    )


@app.command("top-tracks")
@async_command
async def artist_top_tracks(
    artist_id: Annotated[str, typer.Argument(help="Spotify artist ID.")],
    fields: FieldsOption = None,
) -> None:
    async with spotify_client() as spotify:
        result = await spotify.artists.top_tracks(
            artist_id, market=default_market() or "US"
        )
    print_result(
        result,
        columns=TRACK_COLUMNS,
        fields=fields,
    )


@app.command("albums")
@async_command
async def artist_albums(
    artist_id: Annotated[str, typer.Argument(help="Spotify artist ID.")],
    include_groups: Annotated[
        str | None,
        typer.Option("--include-groups", help="album,single,appears_on,compilation"),
    ] = None,
    limit: LimitOption = 20,
    fields: FieldsOption = None,
) -> None:
    async with spotify_client() as spotify:
        result = await spotify.artists.albums(
            artist_id,
            include_groups=include_groups,
            market=default_market(),
            limit=limit,
        )
    print_result(
        result,
        columns=ALBUM_COLUMNS,
        fields=fields,
    )


@app.command("related")
@async_command
async def related_artists(
    artist_id: Annotated[str, typer.Argument(help="Spotify artist ID.")],
    fields: FieldsOption = None,
) -> None:
    async with spotify_client() as spotify:
        result = await spotify.artists.related(artist_id)
    print_result(
        result,
        columns=COLUMNS,
        fields=fields,
    )
