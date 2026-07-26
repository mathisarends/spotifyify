from __future__ import annotations

from collections.abc import Awaitable, Callable, Sequence
from typing import Annotated

import typer

from spotifyify import Spotifyify, SpotifyScope

from ._aliases import AliasGroup
from ._core import (
    BATCH_FOLLOW,
    Jsonable,
    _coalesce_scopes,
    _merge_scopes,
    _sequential_batches,
    _split_values,
)
from ._options import (
    FieldsOption,
    FormatOption,
    IdsArgument,
    JsonOption,
    LimitOption,
    RawOption,
    ScopeOption,
    SortOption,
    WhereOption,
    _handle,
    _render,
)

app = typer.Typer(
    help="Work with Spotify users and following.",
    cls=AliasGroup,
    rich_markup_mode=None,
    no_args_is_help=True,
)

COLUMNS = ("id", "display_name", "uri")
FOLLOWING_COLUMNS = ("id", "following")

READ_SCOPES = [SpotifyScope.USER_LIBRARY_READ.value]
MODIFY_SCOPES = [SpotifyScope.USER_LIBRARY_MODIFY.value]
# follow/unfollow report the resulting state, so they read it back too.
WRITE_SCOPES = _merge_scopes(MODIFY_SCOPES, READ_SCOPES)


def _follow_action(
    type: str,
    ids: Sequence[str],
    *,
    action: Callable[[Spotifyify, list[str]], Awaitable[None]],
    scope: Sequence[str] | None,
    fmt: str | None,
    json_output: bool,
    raw: bool,
    fields: Sequence[str] | None,
) -> None:
    """Apply a follow mutation and report the resulting following state."""
    item_ids = _split_values(ids)

    async def command(spotify: Spotifyify) -> Jsonable:
        await _sequential_batches(
            lambda chunk: action(spotify, chunk), item_ids, BATCH_FOLLOW
        )
        following = await spotify.users.check_following(type, item_ids)
        return [
            {"id": item_id, "following": is_following}
            for item_id, is_following in zip(item_ids, following, strict=False)
        ]

    result = _handle(command, scopes=_coalesce_scopes(scope) or WRITE_SCOPES)
    _render(
        result,
        columns=FOLLOWING_COLUMNS,
        fmt=fmt,
        json_output=json_output,
        raw=raw,
        fields=fields,
    )


@app.command("me")
def users_me(
    fmt: FormatOption = None,
    json_output: JsonOption = False,
    raw: RawOption = False,
    fields: FieldsOption = None,
    scope: ScopeOption = None,
) -> None:
    result = _handle(lambda spotify: spotify.users.me(), scopes=_coalesce_scopes(scope))
    _render(
        result,
        columns=COLUMNS,
        fmt=fmt,
        json_output=json_output,
        raw=raw,
        fields=fields,
    )


@app.command("get")
def users_get(
    user_id: Annotated[str, typer.Argument(help="Spotify user ID.")],
    fmt: FormatOption = None,
    json_output: JsonOption = False,
    raw: RawOption = False,
    fields: FieldsOption = None,
    scope: ScopeOption = None,
) -> None:
    result = _handle(
        lambda spotify: spotify.users.get(user_id), scopes=_coalesce_scopes(scope)
    )
    _render(
        result,
        columns=COLUMNS,
        fmt=fmt,
        json_output=json_output,
        raw=raw,
        fields=fields,
    )


@app.command("following")
def users_following(
    type: Annotated[str, typer.Option("--type")] = "artist",
    limit: LimitOption = 20,
    after: Annotated[str | None, typer.Option("--after")] = None,
    fmt: FormatOption = None,
    json_output: JsonOption = False,
    raw: RawOption = False,
    fields: FieldsOption = None,
    sort: SortOption = None,
    where: WhereOption = None,
    scope: ScopeOption = None,
) -> None:
    result = _handle(
        lambda spotify: spotify.users.following(type=type, limit=limit, after=after),
        scopes=_coalesce_scopes(scope) or READ_SCOPES,
    )
    _render(
        result,
        columns=("id", "name", "uri"),
        fmt=fmt,
        json_output=json_output,
        raw=raw,
        fields=fields,
        sort=sort,
        where=where,
    )


@app.command("follow")
def users_follow(
    type: Annotated[str, typer.Argument(help="artist or user")],
    ids: IdsArgument,
    fmt: FormatOption = None,
    json_output: JsonOption = False,
    raw: RawOption = False,
    fields: FieldsOption = None,
    scope: ScopeOption = None,
) -> None:
    _follow_action(
        type,
        ids,
        action=lambda spotify, chunk: spotify.users.follow(type, chunk),
        scope=scope,
        fmt=fmt,
        json_output=json_output,
        raw=raw,
        fields=fields,
    )


@app.command("unfollow")
def users_unfollow(
    type: Annotated[str, typer.Argument(help="artist or user")],
    ids: IdsArgument,
    fmt: FormatOption = None,
    json_output: JsonOption = False,
    raw: RawOption = False,
    fields: FieldsOption = None,
    scope: ScopeOption = None,
) -> None:
    _follow_action(
        type,
        ids,
        action=lambda spotify, chunk: spotify.users.unfollow(type, chunk),
        scope=scope,
        fmt=fmt,
        json_output=json_output,
        raw=raw,
        fields=fields,
    )


@app.command("check-following")
def users_check_following(
    type: Annotated[str, typer.Argument(help="artist or user")],
    ids: IdsArgument,
    fmt: FormatOption = None,
    json_output: JsonOption = False,
    raw: RawOption = False,
    fields: FieldsOption = None,
    scope: ScopeOption = None,
) -> None:
    item_ids = _split_values(ids)
    result = _handle(
        lambda spotify: spotify.users.check_following(type, item_ids),
        scopes=_coalesce_scopes(scope) or READ_SCOPES,
    )
    payload = [
        {"id": item_id, "following": following}
        for item_id, following in zip(item_ids, result, strict=False)
    ]
    _render(
        payload,
        columns=FOLLOWING_COLUMNS,
        fmt=fmt,
        json_output=json_output,
        raw=raw,
        fields=fields,
    )
