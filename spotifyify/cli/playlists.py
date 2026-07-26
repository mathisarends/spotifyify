from __future__ import annotations

from typing import Annotated

import typer

from spotifyify import SpotifyScope

from ._aliases import AliasGroup
from ._core import _coalesce_scopes, _split_values, spotify_client
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
    async_command,
    print_result,
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


@app.command("search")
@async_command
async def search_playlists(
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
    async with spotify_client(_coalesce_scopes(scope)) as spotify:
        result = await spotify.playlists.find(query, limit=limit, offset=offset)
    print_result(
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
@async_command
async def get_playlist(
    playlist_id: Annotated[str, typer.Argument(help="Spotify playlist ID.")],
    market: MarketOption = None,
    fmt: FormatOption = None,
    json_output: JsonOption = False,
    raw: RawOption = False,
    fields: FieldsOption = None,
    scope: ScopeOption = None,
) -> None:
    async with spotify_client(_coalesce_scopes(scope)) as spotify:
        result = await spotify.playlists.get(playlist_id, market=market)
    print_result(
        result,
        columns=COLUMNS,
        fmt=fmt,
        json_output=json_output,
        raw=raw,
        fields=fields,
    )


@app.command("list")
@async_command
async def list_playlists(
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
    async with spotify_client(
        _coalesce_scopes(scope) or [SpotifyScope.PLAYLIST_READ_PRIVATE.value]
    ) as spotify:
        result = await spotify.playlists.list(
            user_id=user_id, limit=limit, offset=offset
        )
    print_result(
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
@async_command
async def playlist_tracks(
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
    async with spotify_client(_coalesce_scopes(scope)) as spotify:
        result = await spotify.playlists.tracks(
            playlist_id,
            market=market,
            fields=fields_query,
            limit=limit,
            offset=offset,
            additional_types=_split_values(additional_types) or None,
        )
    print_result(
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
@async_command
async def create_playlist(
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
    async with spotify_client(_coalesce_scopes(scope) or _MODIFY_SCOPES) as spotify:
        result = await spotify.playlists.create(
            name,
            public=public,
            collaborative=collaborative,
            description=description,
            user_id=user_id,
        )
    print_result(
        result,
        columns=COLUMNS,
        fmt=fmt,
        json_output=json_output,
        raw=raw,
        fields=fields,
    )


@app.command("update")
@async_command
async def update_playlist(
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
    async with spotify_client(_coalesce_scopes(scope) or _MODIFY_SCOPES) as spotify:
        await spotify.playlists.update(
            playlist_id,
            name=name,
            public=public,
            collaborative=collaborative,
            description=description,
        )
        result = await spotify.playlists.get(playlist_id)
    print_result(
        result,
        columns=("id", "name", "public", "collaborative", "description"),
        fmt=fmt,
        json_output=json_output,
        raw=raw,
        fields=fields,
    )


@app.command("add")
@async_command
async def add_playlist_items(
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
    async with spotify_client(_coalesce_scopes(scope) or _MODIFY_SCOPES) as spotify:
        snapshot_id = await spotify.playlists.add(
            playlist_id, _split_values(uris), position=position
        )
        playlist = await spotify.playlists.get(playlist_id)
    result = {
        "playlist_id": playlist_id,
        "snapshot_id": snapshot_id,
        "total": getattr(getattr(playlist, "tracks", None), "total", None),
        "name": getattr(playlist, "name", None),
    }
    print_result(
        result,
        columns=SNAPSHOT_COLUMNS,
        fmt=fmt,
        json_output=json_output,
        raw=raw,
        fields=fields,
    )


@app.command("replace")
@async_command
async def replace_playlist_items(
    playlist_id: Annotated[str, typer.Argument(help="Spotify playlist ID.")],
    uris: UrisArgument,
    fmt: FormatOption = None,
    json_output: JsonOption = False,
    raw: RawOption = False,
    fields: FieldsOption = None,
    scope: ScopeOption = None,
) -> None:
    async with spotify_client(_coalesce_scopes(scope) or _MODIFY_SCOPES) as spotify:
        snapshot_id = await spotify.playlists.replace(playlist_id, _split_values(uris))
        playlist = await spotify.playlists.get(playlist_id)
    result = {
        "playlist_id": playlist_id,
        "snapshot_id": snapshot_id,
        "total": getattr(getattr(playlist, "tracks", None), "total", None),
        "name": getattr(playlist, "name", None),
    }
    print_result(
        result,
        columns=SNAPSHOT_COLUMNS,
        fmt=fmt,
        json_output=json_output,
        raw=raw,
        fields=fields,
    )


@app.command("remove")
@async_command
async def remove_playlist_items(
    playlist_id: Annotated[str, typer.Argument(help="Spotify playlist ID.")],
    uris: UrisArgument,
    fmt: FormatOption = None,
    json_output: JsonOption = False,
    raw: RawOption = False,
    fields: FieldsOption = None,
    scope: ScopeOption = None,
) -> None:
    async with spotify_client(_coalesce_scopes(scope) or _MODIFY_SCOPES) as spotify:
        snapshot_id = await spotify.playlists.remove(playlist_id, _split_values(uris))
        playlist = await spotify.playlists.get(playlist_id)
    result = {
        "playlist_id": playlist_id,
        "snapshot_id": snapshot_id,
        "total": getattr(getattr(playlist, "tracks", None), "total", None),
        "name": getattr(playlist, "name", None),
    }
    print_result(
        result,
        columns=SNAPSHOT_COLUMNS,
        fmt=fmt,
        json_output=json_output,
        raw=raw,
        fields=fields,
    )


@app.command("reorder")
@async_command
async def reorder_playlist_items(
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
    async with spotify_client(_coalesce_scopes(scope) or _MODIFY_SCOPES) as spotify:
        new_snapshot_id = await spotify.playlists.reorder(
            playlist_id,
            range_start=range_start,
            insert_before=insert_before,
            range_length=range_length,
            snapshot_id=snapshot_id,
        )
        playlist = await spotify.playlists.get(playlist_id)
    result = {
        "playlist_id": playlist_id,
        "snapshot_id": new_snapshot_id,
        "total": getattr(getattr(playlist, "tracks", None), "total", None),
        "name": getattr(playlist, "name", None),
    }
    print_result(
        result,
        columns=SNAPSHOT_COLUMNS,
        fmt=fmt,
        json_output=json_output,
        raw=raw,
        fields=fields,
    )


@app.command("cover-image")
@async_command
async def playlist_cover_image(
    playlist_id: Annotated[str, typer.Argument(help="Spotify playlist ID.")],
    fmt: FormatOption = None,
    json_output: JsonOption = False,
    raw: RawOption = False,
    fields: FieldsOption = None,
    sort: SortOption = None,
    scope: ScopeOption = None,
) -> None:
    async with spotify_client(_coalesce_scopes(scope)) as spotify:
        result = await spotify.playlists.cover_image(playlist_id)
    print_result(
        result,
        columns=("url", "width", "height"),
        fmt=fmt,
        json_output=json_output,
        raw=raw,
        fields=fields,
        sort=sort,
    )
