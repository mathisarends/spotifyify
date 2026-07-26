from typing import Annotated

import typer

from spotifyify import SpotifyScope

from .core import (
    BATCH_ALBUMS,
    BATCH_EPISODES,
    BATCH_SHOWS,
    BATCH_TRACKS,
    default_market,
    merge_scopes,
    sequential_batches,
    split_values,
    spotify_client,
)
from .options import (
    FieldsOption,
    IdsArgument,
    LimitOption,
    async_command,
    print_result,
)

app = typer.Typer(
    help="Work with the current user's library.",
    rich_markup_mode=None,
    no_args_is_help=True,
)

SAVED_COLUMNS = ("id", "saved")

READ_SCOPES = [SpotifyScope.USER_LIBRARY_READ]
MODIFY_SCOPES = [SpotifyScope.USER_LIBRARY_MODIFY]
# Save/remove report the resulting saved state, so they read it back too.
WRITE_SCOPES = merge_scopes(MODIFY_SCOPES, READ_SCOPES)


@app.command("saved-tracks")
@async_command
async def saved_tracks(
    limit: LimitOption = 20,
    fields: FieldsOption = None,
) -> None:
    async with spotify_client(READ_SCOPES) as spotify:
        result = await spotify.library.saved_tracks(
            limit=limit, market=default_market()
        )
    print_result(
        result,
        columns=("track.id", "track.name", "track.artists", "added_at"),
        fields=fields,
    )


@app.command("saved-albums")
@async_command
async def saved_albums(
    limit: LimitOption = 20,
    fields: FieldsOption = None,
) -> None:
    async with spotify_client(READ_SCOPES) as spotify:
        result = await spotify.library.saved_albums(
            limit=limit, market=default_market()
        )
    print_result(
        result,
        columns=("album.id", "album.name", "album.artists", "added_at"),
        fields=fields,
    )


@app.command("saved-shows")
@async_command
async def saved_shows(
    limit: LimitOption = 20,
    fields: FieldsOption = None,
) -> None:
    async with spotify_client(READ_SCOPES) as spotify:
        result = await spotify.library.saved_shows(limit=limit)
    print_result(
        result,
        columns=("show.id", "show.name", "show.publisher", "added_at"),
        fields=fields,
    )


@app.command("saved-episodes")
@async_command
async def saved_episodes(
    limit: LimitOption = 20,
    fields: FieldsOption = None,
) -> None:
    async with spotify_client(READ_SCOPES) as spotify:
        result = await spotify.library.saved_episodes(limit=limit)
    print_result(
        result,
        columns=("episode.id", "episode.name", "added_at"),
        fields=fields,
    )


@app.command("top-tracks")
@async_command
async def library_top_tracks(
    time_range: Annotated[str, typer.Option("--time-range")] = "medium_term",
    limit: LimitOption = 20,
    fields: FieldsOption = None,
) -> None:
    async with spotify_client([SpotifyScope.USER_TOP_READ]) as spotify:
        result = await spotify.library.top_tracks(time_range=time_range, limit=limit)
    print_result(
        result,
        columns=("id", "name", "artists", "uri"),
        fields=fields,
    )


@app.command("top-artists")
@async_command
async def library_top_artists(
    time_range: Annotated[str, typer.Option("--time-range")] = "medium_term",
    limit: LimitOption = 20,
    fields: FieldsOption = None,
) -> None:
    async with spotify_client([SpotifyScope.USER_TOP_READ]) as spotify:
        result = await spotify.library.top_artists(time_range=time_range, limit=limit)
    print_result(
        result,
        columns=("id", "name", "uri"),
        fields=fields,
    )


@app.command("save-tracks")
@async_command
async def save_tracks(
    track_ids: IdsArgument,
    fields: FieldsOption = None,
) -> None:
    ids = split_values(track_ids)
    async with spotify_client(WRITE_SCOPES) as spotify:
        await sequential_batches(spotify.library.save_tracks, ids, BATCH_TRACKS)
        saved = await spotify.library.check_tracks(ids)
    result = [
        {"id": item_id, "saved": is_saved}
        for item_id, is_saved in zip(ids, saved, strict=False)
    ]
    print_result(
        result,
        columns=SAVED_COLUMNS,
        fields=fields,
    )


@app.command("remove-tracks")
@async_command
async def remove_tracks(
    track_ids: IdsArgument,
    fields: FieldsOption = None,
) -> None:
    ids = split_values(track_ids)
    async with spotify_client(WRITE_SCOPES) as spotify:
        await sequential_batches(spotify.library.remove_tracks, ids, BATCH_TRACKS)
        saved = await spotify.library.check_tracks(ids)
    result = [
        {"id": item_id, "saved": is_saved}
        for item_id, is_saved in zip(ids, saved, strict=False)
    ]
    print_result(
        result,
        columns=SAVED_COLUMNS,
        fields=fields,
    )


@app.command("check-tracks")
@async_command
async def check_tracks(
    track_ids: IdsArgument,
    fields: FieldsOption = None,
) -> None:
    ids = split_values(track_ids)
    async with spotify_client(READ_SCOPES) as spotify:
        saved = await spotify.library.check_tracks(ids)
    result = [
        {"id": item_id, "saved": is_saved}
        for item_id, is_saved in zip(ids, saved, strict=False)
    ]
    print_result(
        result,
        columns=SAVED_COLUMNS,
        fields=fields,
    )


@app.command("save-albums")
@async_command
async def save_albums(
    album_ids: IdsArgument,
    fields: FieldsOption = None,
) -> None:
    ids = split_values(album_ids)
    async with spotify_client(WRITE_SCOPES) as spotify:
        await sequential_batches(spotify.library.save_albums, ids, BATCH_ALBUMS)
        saved = await spotify.library.check_albums(ids)
    result = [
        {"id": item_id, "saved": is_saved}
        for item_id, is_saved in zip(ids, saved, strict=False)
    ]
    print_result(
        result,
        columns=SAVED_COLUMNS,
        fields=fields,
    )


@app.command("remove-albums")
@async_command
async def remove_albums(
    album_ids: IdsArgument,
    fields: FieldsOption = None,
) -> None:
    ids = split_values(album_ids)
    async with spotify_client(WRITE_SCOPES) as spotify:
        await sequential_batches(spotify.library.remove_albums, ids, BATCH_ALBUMS)
        saved = await spotify.library.check_albums(ids)
    result = [
        {"id": item_id, "saved": is_saved}
        for item_id, is_saved in zip(ids, saved, strict=False)
    ]
    print_result(
        result,
        columns=SAVED_COLUMNS,
        fields=fields,
    )


@app.command("check-albums")
@async_command
async def check_albums(
    album_ids: IdsArgument,
    fields: FieldsOption = None,
) -> None:
    ids = split_values(album_ids)
    async with spotify_client(READ_SCOPES) as spotify:
        saved = await spotify.library.check_albums(ids)
    result = [
        {"id": item_id, "saved": is_saved}
        for item_id, is_saved in zip(ids, saved, strict=False)
    ]
    print_result(
        result,
        columns=SAVED_COLUMNS,
        fields=fields,
    )


@app.command("save-shows")
@async_command
async def save_shows(
    show_ids: IdsArgument,
    fields: FieldsOption = None,
) -> None:
    ids = split_values(show_ids)
    async with spotify_client(WRITE_SCOPES) as spotify:
        await sequential_batches(spotify.library.save_shows, ids, BATCH_SHOWS)
        saved = await spotify.library.check_shows(ids)
    result = [
        {"id": item_id, "saved": is_saved}
        for item_id, is_saved in zip(ids, saved, strict=False)
    ]
    print_result(
        result,
        columns=SAVED_COLUMNS,
        fields=fields,
    )


@app.command("remove-shows")
@async_command
async def remove_shows(
    show_ids: IdsArgument,
    fields: FieldsOption = None,
) -> None:
    ids = split_values(show_ids)
    async with spotify_client(WRITE_SCOPES) as spotify:
        await sequential_batches(spotify.library.remove_shows, ids, BATCH_SHOWS)
        saved = await spotify.library.check_shows(ids)
    result = [
        {"id": item_id, "saved": is_saved}
        for item_id, is_saved in zip(ids, saved, strict=False)
    ]
    print_result(
        result,
        columns=SAVED_COLUMNS,
        fields=fields,
    )


@app.command("check-shows")
@async_command
async def check_shows(
    show_ids: IdsArgument,
    fields: FieldsOption = None,
) -> None:
    ids = split_values(show_ids)
    async with spotify_client(READ_SCOPES) as spotify:
        saved = await spotify.library.check_shows(ids)
    result = [
        {"id": item_id, "saved": is_saved}
        for item_id, is_saved in zip(ids, saved, strict=False)
    ]
    print_result(
        result,
        columns=SAVED_COLUMNS,
        fields=fields,
    )


@app.command("save-episodes")
@async_command
async def save_episodes(
    episode_ids: IdsArgument,
    fields: FieldsOption = None,
) -> None:
    ids = split_values(episode_ids)
    async with spotify_client(WRITE_SCOPES) as spotify:
        await sequential_batches(spotify.library.save_episodes, ids, BATCH_EPISODES)
        saved = await spotify.library.check_episodes(ids)
    result = [
        {"id": item_id, "saved": is_saved}
        for item_id, is_saved in zip(ids, saved, strict=False)
    ]
    print_result(
        result,
        columns=SAVED_COLUMNS,
        fields=fields,
    )


@app.command("remove-episodes")
@async_command
async def remove_episodes(
    episode_ids: IdsArgument,
    fields: FieldsOption = None,
) -> None:
    ids = split_values(episode_ids)
    async with spotify_client(WRITE_SCOPES) as spotify:
        await sequential_batches(spotify.library.remove_episodes, ids, BATCH_EPISODES)
        saved = await spotify.library.check_episodes(ids)
    result = [
        {"id": item_id, "saved": is_saved}
        for item_id, is_saved in zip(ids, saved, strict=False)
    ]
    print_result(
        result,
        columns=SAVED_COLUMNS,
        fields=fields,
    )


@app.command("check-episodes")
@async_command
async def check_episodes(
    episode_ids: IdsArgument,
    fields: FieldsOption = None,
) -> None:
    ids = split_values(episode_ids)
    async with spotify_client(READ_SCOPES) as spotify:
        saved = await spotify.library.check_episodes(ids)
    result = [
        {"id": item_id, "saved": is_saved}
        for item_id, is_saved in zip(ids, saved, strict=False)
    ]
    print_result(
        result,
        columns=SAVED_COLUMNS,
        fields=fields,
    )
