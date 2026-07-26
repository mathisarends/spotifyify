from __future__ import annotations

from typing import Annotated, Any

import typer

from spotifyify import Spotifyify, SpotifyScope

from ._aliases import AliasGroup
from ._core import _coalesce_scopes, _split_values
from ._options import (
    DEFAULT_LIMIT,
    FieldsOption,
    FormatOption,
    JsonOption,
    LimitOption,
    MarketOption,
    OffsetOption,
    RawOption,
    ScopeOption,
    SortOption,
    UrisArgument,
    WhereOption,
    _handle,
    _render,
)

app = typer.Typer(
    help="Work with Spotify playlists.",
    cls=AliasGroup,
    rich_markup_mode=None,
    no_args_is_help=True,
)

COLUMNS = ("id", "name", "owner", "uri")
SNAPSHOT_COLUMNS = ("playlist_id", "snapshot_id", "total")

_MODIFY_SCOPES = [
    SpotifyScope.PLAYLIST_MODIFY_PUBLIC.value,
    SpotifyScope.PLAYLIST_MODIFY_PRIVATE.value,
]


def _mutate_items(
    action,
    *,
    playlist_id: str,
    scope,
    fmt: str | None,
    json_output: bool,
    raw: bool,
    fields,
) -> None:
    """Run a playlist mutation and report the resulting snapshot and length."""

    async def command(spotify: Spotifyify) -> Any:
        snapshot_id = await action(spotify)
        playlist = await spotify.playlists.get(playlist_id)
        return {
            "playlist_id": playlist_id,
            "snapshot_id": snapshot_id,
            "total": getattr(getattr(playlist, "tracks", None), "total", None),
            "name": getattr(playlist, "name", None),
        }

    result = _handle(command, scopes=_coalesce_scopes(scope) or _MODIFY_SCOPES)
    _render(
        result,
        columns=SNAPSHOT_COLUMNS,
        fmt=fmt,
        json_output=json_output,
        raw=raw,
        fields=fields,
    )


@app.command("search")
def search_playlists(
    query: Annotated[str, typer.Argument(help="Spotify search query.")],
    limit: LimitOption = DEFAULT_LIMIT,
    offset: OffsetOption = 0,
    fmt: FormatOption = None,
    json_output: JsonOption = False,
    raw: RawOption = False,
    fields: FieldsOption = None,
    sort: SortOption = None,
    where: WhereOption = None,
    scope: ScopeOption = None,
) -> None:
    result = _handle(
        lambda spotify: spotify.playlists.find(query, limit=limit, offset=offset),
        scopes=_coalesce_scopes(scope),
    )
    _render(
        result,
        columns=COLUMNS,
        fmt=fmt,
        json_output=json_output,
        raw=raw,
        fields=fields,
        sort=sort,
        where=where,
    )


@app.command("get")
def get_playlist(
    playlist_id: Annotated[str, typer.Argument(help="Spotify playlist ID.")],
    market: MarketOption = None,
    fmt: FormatOption = None,
    json_output: JsonOption = False,
    raw: RawOption = False,
    fields: FieldsOption = None,
    scope: ScopeOption = None,
) -> None:
    result = _handle(
        lambda spotify: spotify.playlists.get(playlist_id, market=market),
        scopes=_coalesce_scopes(scope),
    )
    _render(
        result,
        columns=COLUMNS,
        fmt=fmt,
        json_output=json_output,
        raw=raw,
        fields=fields,
    )


@app.command("list")
def list_playlists(
    user_id: Annotated[str | None, typer.Option("--user-id", "-u")] = None,
    limit: LimitOption = 20,
    offset: OffsetOption = 0,
    fmt: FormatOption = None,
    json_output: JsonOption = False,
    raw: RawOption = False,
    fields: FieldsOption = None,
    sort: SortOption = None,
    where: WhereOption = None,
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
        columns=COLUMNS,
        fmt=fmt,
        json_output=json_output,
        raw=raw,
        fields=fields,
        sort=sort,
        where=where,
    )


@app.command("tracks")
def playlist_tracks(
    playlist_id: Annotated[str, typer.Argument(help="Spotify playlist ID.")],
    market: MarketOption = None,
    fields_query: Annotated[
        str | None,
        typer.Option(
            "--spotify-fields",
            help="Server-side field filter applied by Spotify before the response is sent.",
        ),
    ] = None,
    limit: LimitOption = 20,
    offset: OffsetOption = 0,
    additional_types: Annotated[
        list[str] | None, typer.Option("--additional-type")
    ] = None,
    fmt: FormatOption = None,
    json_output: JsonOption = False,
    raw: RawOption = False,
    fields: FieldsOption = None,
    sort: SortOption = None,
    where: WhereOption = None,
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
        columns=("track.id", "track.name", "track.artists", "added_at"),
        fmt=fmt,
        json_output=json_output,
        raw=raw,
        fields=fields,
        sort=sort,
        where=where,
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
    fmt: FormatOption = None,
    json_output: JsonOption = False,
    raw: RawOption = False,
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
        columns=COLUMNS,
        fmt=fmt,
        json_output=json_output,
        raw=raw,
        fields=fields,
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
    fmt: FormatOption = None,
    json_output: JsonOption = False,
    raw: RawOption = False,
    fields: FieldsOption = None,
    scope: ScopeOption = None,
) -> None:
    async def command(spotify: Spotifyify) -> Any:
        await spotify.playlists.update(
            playlist_id,
            name=name,
            public=public,
            collaborative=collaborative,
            description=description,
        )
        return await spotify.playlists.get(playlist_id)

    result = _handle(command, scopes=_coalesce_scopes(scope) or _MODIFY_SCOPES)
    _render(
        result,
        columns=("id", "name", "public", "collaborative", "description"),
        fmt=fmt,
        json_output=json_output,
        raw=raw,
        fields=fields,
    )


@app.command("add")
def add_playlist_items(
    playlist_id: Annotated[str, typer.Argument(help="Spotify playlist ID.")],
    uris: UrisArgument,
    position: Annotated[int | None, typer.Option("--position")] = None,
    fmt: FormatOption = None,
    json_output: JsonOption = False,
    raw: RawOption = False,
    fields: FieldsOption = None,
    scope: ScopeOption = None,
) -> None:
    """Add one or many URIs in a single call."""
    _mutate_items(
        lambda spotify: spotify.playlists.add(
            playlist_id, _split_values(uris), position=position
        ),
        playlist_id=playlist_id,
        scope=scope,
        fmt=fmt,
        json_output=json_output,
        raw=raw,
        fields=fields,
    )


@app.command("replace")
def replace_playlist_items(
    playlist_id: Annotated[str, typer.Argument(help="Spotify playlist ID.")],
    uris: UrisArgument,
    fmt: FormatOption = None,
    json_output: JsonOption = False,
    raw: RawOption = False,
    fields: FieldsOption = None,
    scope: ScopeOption = None,
) -> None:
    _mutate_items(
        lambda spotify: spotify.playlists.replace(playlist_id, _split_values(uris)),
        playlist_id=playlist_id,
        scope=scope,
        fmt=fmt,
        json_output=json_output,
        raw=raw,
        fields=fields,
    )


@app.command("remove")
def remove_playlist_items(
    playlist_id: Annotated[str, typer.Argument(help="Spotify playlist ID.")],
    uris: UrisArgument,
    fmt: FormatOption = None,
    json_output: JsonOption = False,
    raw: RawOption = False,
    fields: FieldsOption = None,
    scope: ScopeOption = None,
) -> None:
    _mutate_items(
        lambda spotify: spotify.playlists.remove(playlist_id, _split_values(uris)),
        playlist_id=playlist_id,
        scope=scope,
        fmt=fmt,
        json_output=json_output,
        raw=raw,
        fields=fields,
    )


@app.command("reorder")
def reorder_playlist_items(
    playlist_id: Annotated[str, typer.Argument(help="Spotify playlist ID.")],
    range_start: Annotated[int, typer.Option("--range-start", min=0)],
    insert_before: Annotated[int, typer.Option("--insert-before", min=0)],
    range_length: Annotated[int, typer.Option("--range-length", min=1)] = 1,
    snapshot_id: Annotated[str | None, typer.Option("--snapshot-id")] = None,
    fmt: FormatOption = None,
    json_output: JsonOption = False,
    raw: RawOption = False,
    fields: FieldsOption = None,
    scope: ScopeOption = None,
) -> None:
    _mutate_items(
        lambda spotify: spotify.playlists.reorder(
            playlist_id,
            range_start=range_start,
            insert_before=insert_before,
            range_length=range_length,
            snapshot_id=snapshot_id,
        ),
        playlist_id=playlist_id,
        scope=scope,
        fmt=fmt,
        json_output=json_output,
        raw=raw,
        fields=fields,
    )


@app.command("cover-image")
def playlist_cover_image(
    playlist_id: Annotated[str, typer.Argument(help="Spotify playlist ID.")],
    fmt: FormatOption = None,
    json_output: JsonOption = False,
    raw: RawOption = False,
    fields: FieldsOption = None,
    sort: SortOption = None,
    scope: ScopeOption = None,
) -> None:
    result = _handle(
        lambda spotify: spotify.playlists.cover_image(playlist_id),
        scopes=_coalesce_scopes(scope),
    )
    _render(
        result,
        columns=("url", "width", "height"),
        fmt=fmt,
        json_output=json_output,
        raw=raw,
        fields=fields,
        sort=sort,
    )
