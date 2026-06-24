from __future__ import annotations

from typing import Annotated

import typer

from spotifyify import SpotifyScope

from ._core import (
    _coalesce_scopes,
    _print_json,
    _print_success,
    _print_table,
    _split_values,
)
from ._options import (
    FieldsOption,
    IdsArgument,
    JsonOption,
    LimitOption,
    ScopeOption,
    _handle,
    _render,
)

app = typer.Typer(help="Work with Spotify users and following.")


@app.command("me")
def users_me(
    json_output: JsonOption = False,
    fields: FieldsOption = None,
    scope: ScopeOption = None,
) -> None:
    result = _handle(lambda spotify: spotify.users.me(), scopes=_coalesce_scopes(scope))
    _render(
        result,
        json_output=json_output,
        fields=fields,
        columns=("id", "display_name", "uri"),
    )


@app.command("get")
def users_get(
    user_id: Annotated[str, typer.Argument(help="Spotify user ID.")],
    json_output: JsonOption = False,
    fields: FieldsOption = None,
    scope: ScopeOption = None,
) -> None:
    result = _handle(
        lambda spotify: spotify.users.get(user_id), scopes=_coalesce_scopes(scope)
    )
    _render(
        result,
        json_output=json_output,
        fields=fields,
        columns=("id", "display_name", "uri"),
    )


@app.command("following")
def users_following(
    type: Annotated[str, typer.Option("--type")] = "artist",
    limit: LimitOption = 20,
    after: Annotated[str | None, typer.Option("--after")] = None,
    json_output: JsonOption = False,
    fields: FieldsOption = None,
    scope: ScopeOption = None,
) -> None:
    result = _handle(
        lambda spotify: spotify.users.following(type=type, limit=limit, after=after),
        scopes=_coalesce_scopes(scope) or [SpotifyScope.USER_LIBRARY_READ.value],
    )
    _render(
        result,
        json_output=json_output,
        fields=fields,
        columns=("id", "name", "uri"),
    )


@app.command("follow")
def users_follow(
    type: Annotated[str, typer.Argument(help="artist or user")],
    ids: IdsArgument,
    scope: ScopeOption = None,
) -> None:
    _handle(
        lambda spotify: spotify.users.follow(type, _split_values(ids)),
        scopes=_coalesce_scopes(scope) or [SpotifyScope.USER_LIBRARY_MODIFY.value],
    )
    _print_success()


@app.command("unfollow")
def users_unfollow(
    type: Annotated[str, typer.Argument(help="artist or user")],
    ids: IdsArgument,
    scope: ScopeOption = None,
) -> None:
    _handle(
        lambda spotify: spotify.users.unfollow(type, _split_values(ids)),
        scopes=_coalesce_scopes(scope) or [SpotifyScope.USER_LIBRARY_MODIFY.value],
    )
    _print_success()


@app.command("check-following")
def users_check_following(
    type: Annotated[str, typer.Argument(help="artist or user")],
    ids: IdsArgument,
    json_output: JsonOption = False,
    scope: ScopeOption = None,
) -> None:
    item_ids = _split_values(ids)
    result = _handle(
        lambda spotify: spotify.users.check_following(type, item_ids),
        scopes=_coalesce_scopes(scope) or [SpotifyScope.USER_LIBRARY_READ.value],
    )
    payload = [
        {"id": item_id, "following": following}
        for item_id, following in zip(item_ids, result, strict=False)
    ]
    (
        _print_json(payload)
        if json_output
        else _print_table(payload, ("id", "following"))
    )
