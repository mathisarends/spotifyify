from __future__ import annotations

from typing import Annotated

import typer

from spotifyify import SpotifyScope

from .core import (
    BATCH_FOLLOW,
    _merge_scopes,
    _sequential_batches,
    _split_values,
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
    help="Work with Spotify users and following.",
    rich_markup_mode=None,
    no_args_is_help=True,
)

COLUMNS = ("id", "display_name", "uri")
FOLLOWING_COLUMNS = ("id", "following")

READ_SCOPES = [SpotifyScope.USER_LIBRARY_READ]
MODIFY_SCOPES = [SpotifyScope.USER_LIBRARY_MODIFY]
# follow/unfollow report the resulting state, so they read it back too.
WRITE_SCOPES = _merge_scopes(MODIFY_SCOPES, READ_SCOPES)


@app.command("me")
@async_command
async def users_me(
    fields: FieldsOption = None,
) -> None:
    async with spotify_client() as spotify:
        result = await spotify.users.me()
    print_result(
        result,
        columns=COLUMNS,
        fields=fields,
    )


@app.command("get")
@async_command
async def users_get(
    user_id: Annotated[str, typer.Argument(help="Spotify user ID.")],
    fields: FieldsOption = None,
) -> None:
    async with spotify_client() as spotify:
        result = await spotify.users.get(user_id)
    print_result(
        result,
        columns=COLUMNS,
        fields=fields,
    )


@app.command("following")
@async_command
async def users_following(
    type: Annotated[str, typer.Option("--type")] = "artist",
    limit: LimitOption = 20,
    after: Annotated[str | None, typer.Option("--after")] = None,
    fields: FieldsOption = None,
) -> None:
    async with spotify_client(READ_SCOPES) as spotify:
        result = await spotify.users.following(type=type, limit=limit, after=after)
    print_result(
        result,
        columns=("id", "name", "uri"),
        fields=fields,
    )


@app.command("follow")
@async_command
async def users_follow(
    type: Annotated[str, typer.Argument(help="artist or user")],
    ids: IdsArgument,
    fields: FieldsOption = None,
) -> None:
    item_ids = _split_values(ids)
    async with spotify_client(WRITE_SCOPES) as spotify:
        await _sequential_batches(
            lambda chunk: spotify.users.follow(type, chunk),
            item_ids,
            BATCH_FOLLOW,
        )
        following = await spotify.users.check_following(type, item_ids)
    result = [
        {"id": item_id, "following": is_following}
        for item_id, is_following in zip(item_ids, following, strict=False)
    ]
    print_result(
        result,
        columns=FOLLOWING_COLUMNS,
        fields=fields,
    )


@app.command("unfollow")
@async_command
async def users_unfollow(
    type: Annotated[str, typer.Argument(help="artist or user")],
    ids: IdsArgument,
    fields: FieldsOption = None,
) -> None:
    item_ids = _split_values(ids)
    async with spotify_client(WRITE_SCOPES) as spotify:
        await _sequential_batches(
            lambda chunk: spotify.users.unfollow(type, chunk),
            item_ids,
            BATCH_FOLLOW,
        )
        following = await spotify.users.check_following(type, item_ids)
    result = [
        {"id": item_id, "following": is_following}
        for item_id, is_following in zip(item_ids, following, strict=False)
    ]
    print_result(
        result,
        columns=FOLLOWING_COLUMNS,
        fields=fields,
    )


@app.command("check-following")
@async_command
async def users_check_following(
    type: Annotated[str, typer.Argument(help="artist or user")],
    ids: IdsArgument,
    fields: FieldsOption = None,
) -> None:
    item_ids = _split_values(ids)
    async with spotify_client(READ_SCOPES) as spotify:
        following_values = await spotify.users.check_following(type, item_ids)
    payload = [
        {"id": item_id, "following": following}
        for item_id, following in zip(item_ids, following_values, strict=False)
    ]
    print_result(
        payload,
        columns=FOLLOWING_COLUMNS,
        fields=fields,
    )
