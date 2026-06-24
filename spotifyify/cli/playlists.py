from __future__ import annotations

from typing import Annotated

import typer

from spotifyify import SpotifyScope

from ._core import _coalesce_scopes, _print_json, _print_success, _split_values
from ._options import (
    DEFAULT_LIMIT,
    FieldsOption,
    JsonOption,
    LimitOption,
    MarketOption,
    OffsetOption,
    ScopeOption,
    UrisArgument,
    _handle,
    _render,
)

app = typer.Typer(help="Work with Spotify playlists.")

_MODIFY_SCOPES = [
    SpotifyScope.PLAYLIST_MODIFY_PUBLIC.value,
    SpotifyScope.PLAYLIST_MODIFY_PRIVATE.value,
]


@app.command("search")
def search_playlists(
    query: Annotated[str, typer.Argument(help="Spotify search query.")],
    limit: LimitOption = DEFAULT_LIMIT,
    offset: OffsetOption = 0,
    json_output: JsonOption = False,
    fields: FieldsOption = None,
    scope: ScopeOption = None,
) -> None:
    result = _handle(
        lambda spotify: spotify.playlists.find(query, limit=limit, offset=offset),
        scopes=_coalesce_scopes(scope),
    )
    _render(
        result,
        json_output=json_output,
        fields=fields,
        columns=("id", "name", "owner", "uri"),
    )


@app.command("get")
def get_playlist(
    playlist_id: Annotated[str, typer.Argument(help="Spotify playlist ID.")],
    market: MarketOption = None,
    json_output: JsonOption = False,
    fields: FieldsOption = None,
    scope: ScopeOption = None,
) -> None:
    result = _handle(
        lambda spotify: spotify.playlists.get(playlist_id, market=market),
        scopes=_coalesce_scopes(scope),
    )
    _render(
        result,
        json_output=json_output,
        fields=fields,
        columns=("id", "name", "owner", "uri"),
    )


@app.command("list")
def list_playlists(
    user_id: Annotated[str | None, typer.Option("--user-id", "-u")] = None,
    limit: LimitOption = 20,
    offset: OffsetOption = 0,
    json_output: JsonOption = False,
    fields: FieldsOption = None,
    scope: ScopeOption = None,
) -> None:
    result = _handle(
        lambda spotify: spotify.playlists.list(
            user_id=user_id, limit=limit, offset=offset
        ),
        scopes=_coalesce_scopes(scope) or [SpotifyScope.PLAYLIST_READ_PRIVATE.value],
    )
    _render(
        result,
        json_output=json_output,
        fields=fields,
        columns=("id", "name", "owner", "uri"),
    )


@app.command("tracks")
def playlist_tracks(
    playlist_id: Annotated[str, typer.Argument(help="Spotify playlist ID.")],
    market: MarketOption = None,
    fields_query: Annotated[str | None, typer.Option("--spotify-fields")] = None,
    limit: LimitOption = 20,
    offset: OffsetOption = 0,
    additional_types: Annotated[
        list[str] | None, typer.Option("--additional-type")
    ] = None,
    json_output: JsonOption = False,
    fields: FieldsOption = None,
    scope: ScopeOption = None,
) -> None:
    result = _handle(
        lambda spotify: spotify.playlists.tracks(
            playlist_id,
            market=market,
            fields=fields_query,
            limit=limit,
            offset=offset,
            additional_types=_split_values(additional_types) or None,
        ),
        scopes=_coalesce_scopes(scope),
    )
    _render(
        result,
        json_output=json_output,
        fields=fields,
        columns=("item.id", "item.name", "item.artists", "added_at"),
    )


@app.command("create")
def create_playlist(
    name: Annotated[str, typer.Argument(help="Playlist name.")],
    public: Annotated[bool, typer.Option("--public/--private")] = False,
    collaborative: Annotated[
        bool, typer.Option("--collaborative/--not-collaborative")
    ] = False,
    description: Annotated[str, typer.Option("--description", "-d")] = "",
    user_id: Annotated[str | None, typer.Option("--user-id", "-u")] = None,
    json_output: JsonOption = False,
    fields: FieldsOption = None,
    scope: ScopeOption = None,
) -> None:
    result = _handle(
        lambda spotify: spotify.playlists.create(
            name,
            public=public,
            collaborative=collaborative,
            description=description,
            user_id=user_id,
        ),
        scopes=_coalesce_scopes(scope) or _MODIFY_SCOPES,
    )
    _render(
        result,
        json_output=json_output,
        fields=fields,
        columns=("id", "name", "uri"),
    )


@app.command("update")
def update_playlist(
    playlist_id: Annotated[str, typer.Argument(help="Spotify playlist ID.")],
    name: Annotated[str | None, typer.Option("--name")] = None,
    public: Annotated[bool | None, typer.Option("--public/--private")] = None,
    collaborative: Annotated[
        bool | None, typer.Option("--collaborative/--not-collaborative")
    ] = None,
    description: Annotated[str | None, typer.Option("--description", "-d")] = None,
    scope: ScopeOption = None,
) -> None:
    _handle(
        lambda spotify: spotify.playlists.update(
            playlist_id,
            name=name,
            public=public,
            collaborative=collaborative,
            description=description,
        ),
        scopes=_coalesce_scopes(scope) or _MODIFY_SCOPES,
    )
    _print_success()


@app.command("add")
def add_playlist_items(
    playlist_id: Annotated[str, typer.Argument(help="Spotify playlist ID.")],
    uris: UrisArgument,
    position: Annotated[int | None, typer.Option("--position")] = None,
    json_output: JsonOption = False,
    fields: FieldsOption = None,
    scope: ScopeOption = None,
) -> None:
    result = _handle(
        lambda spotify: spotify.playlists.add(
            playlist_id, _split_values(uris), position=position
        ),
        scopes=_coalesce_scopes(scope) or _MODIFY_SCOPES,
    )
    payload = {"snapshot_id": result}
    (
        _print_json(payload, fields=_split_values(fields))
        if json_output
        else _print_success(result)
    )


@app.command("replace")
def replace_playlist_items(
    playlist_id: Annotated[str, typer.Argument(help="Spotify playlist ID.")],
    uris: UrisArgument,
    json_output: JsonOption = False,
    fields: FieldsOption = None,
    scope: ScopeOption = None,
) -> None:
    result = _handle(
        lambda spotify: spotify.playlists.replace(playlist_id, _split_values(uris)),
        scopes=_coalesce_scopes(scope) or _MODIFY_SCOPES,
    )
    payload = {"snapshot_id": result}
    (
        _print_json(payload, fields=_split_values(fields))
        if json_output
        else _print_success(result)
    )


@app.command("remove")
def remove_playlist_items(
    playlist_id: Annotated[str, typer.Argument(help="Spotify playlist ID.")],
    uris: UrisArgument,
    json_output: JsonOption = False,
    fields: FieldsOption = None,
    scope: ScopeOption = None,
) -> None:
    result = _handle(
        lambda spotify: spotify.playlists.remove(playlist_id, _split_values(uris)),
        scopes=_coalesce_scopes(scope) or _MODIFY_SCOPES,
    )
    payload = {"snapshot_id": result}
    (
        _print_json(payload, fields=_split_values(fields))
        if json_output
        else _print_success(result)
    )


@app.command("reorder")
def reorder_playlist_items(
    playlist_id: Annotated[str, typer.Argument(help="Spotify playlist ID.")],
    range_start: Annotated[int, typer.Option("--range-start", min=0)],
    insert_before: Annotated[int, typer.Option("--insert-before", min=0)],
    range_length: Annotated[int, typer.Option("--range-length", min=1)] = 1,
    snapshot_id: Annotated[str | None, typer.Option("--snapshot-id")] = None,
    json_output: JsonOption = False,
    fields: FieldsOption = None,
    scope: ScopeOption = None,
) -> None:
    result = _handle(
        lambda spotify: spotify.playlists.reorder(
            playlist_id,
            range_start=range_start,
            insert_before=insert_before,
            range_length=range_length,
            snapshot_id=snapshot_id,
        ),
        scopes=_coalesce_scopes(scope) or _MODIFY_SCOPES,
    )
    payload = {"snapshot_id": result}
    (
        _print_json(payload, fields=_split_values(fields))
        if json_output
        else _print_success(result)
    )


@app.command("cover-image")
def playlist_cover_image(
    playlist_id: Annotated[str, typer.Argument(help="Spotify playlist ID.")],
    json_output: JsonOption = False,
    fields: FieldsOption = None,
    scope: ScopeOption = None,
) -> None:
    result = _handle(
        lambda spotify: spotify.playlists.cover_image(playlist_id),
        scopes=_coalesce_scopes(scope),
    )
    _render(
        result,
        json_output=json_output,
        fields=fields,
        columns=("url", "width", "height"),
    )
