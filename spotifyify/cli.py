from __future__ import annotations

import asyncio
import json
from collections.abc import Awaitable, Callable, Mapping, Sequence
from typing import Annotated, Any

from pydantic import BaseModel

from spotifyify import SpotifyAPIError, SpotifyAuthError, Spotifyify, SpotifyScope

try:
    import typer
except ImportError:  # pragma: no cover - exercised by installed package users.
    typer = None


Jsonable = BaseModel | list[Any] | dict[str, Any] | str | int | float | bool | None
AsyncCommand = Callable[[Spotifyify], Awaitable[Jsonable]]

DEFAULT_LIMIT = 10
INSTALL_MESSAGE = "Install the CLI dependencies with: uv add spotifyify[cli]"


def main() -> None:
    if typer is None:
        raise SystemExit(INSTALL_MESSAGE)
    app()


def _as_jsonable(value: Jsonable) -> Any:
    if isinstance(value, BaseModel):
        return value.model_dump(mode="json", exclude_none=True)
    if isinstance(value, list):
        return [_as_jsonable(item) for item in value]
    if isinstance(value, dict):
        return {key: _as_jsonable(item) for key, item in value.items()}
    return value


def _split_values(values: Sequence[str] | None) -> list[str]:
    if not values:
        return []
    items: list[str] = []
    for raw_value in values:
        items.extend(value for value in raw_value.replace(",", " ").split() if value)
    return items


def _parse_scopes(scope_values: Sequence[str]) -> list[SpotifyScope | str]:
    scopes: list[SpotifyScope | str] = []
    for value in _split_values(scope_values):
        try:
            scopes.append(SpotifyScope(value))
        except ValueError:
            scopes.append(value)
    return scopes


def _coalesce_scopes(scope_values: Sequence[str] | None) -> Sequence[str]:
    return scope_values or ()


def _parse_json_object(
    raw_value: str | None, option_name: str
) -> dict[str, Any] | None:
    if not raw_value:
        return None
    try:
        value = json.loads(raw_value)
    except json.JSONDecodeError as exc:
        message = f"{option_name} must be a JSON object: {exc.msg}"
        if typer is None:
            raise ValueError(message) from exc
        raise typer.BadParameter(message) from exc
    if not isinstance(value, dict):
        message = f"{option_name} must be a JSON object"
        if typer is None:
            raise ValueError(message)
        raise typer.BadParameter(message)
    return value


def _get_path(value: Any, path: str) -> Any:
    current = value
    for part in path.split("."):
        if isinstance(current, Mapping):
            current = current.get(part)
        elif isinstance(current, Sequence) and not isinstance(current, str):
            try:
                current = current[int(part)]
            except (ValueError, IndexError):
                return None
        else:
            current = getattr(current, part, None)
        if current is None:
            return None
    return current


def _filter_fields(value: Any, fields: Sequence[str]) -> Any:
    if not fields:
        return value
    if isinstance(value, list):
        return [_filter_fields(item, fields) for item in value]
    return {field: _get_path(value, field) for field in fields}


def _format_value(value: Any) -> str:
    value = _as_jsonable(value)
    if value is None:
        return ""
    if isinstance(value, list):
        return ", ".join(_format_value(item) for item in value)
    if isinstance(value, dict):
        if "name" in value:
            return str(value["name"])
        if "id" in value:
            return str(value["id"])
        return json.dumps(value, ensure_ascii=False, separators=(",", ":"))
    return str(value)


def _items(value: Any) -> list[Any]:
    value = _as_jsonable(value)
    if isinstance(value, dict) and isinstance(value.get("items"), list):
        return value["items"]
    if isinstance(value, dict) and isinstance(value.get("queue"), list):
        return value["queue"]
    if isinstance(value, list):
        return value
    if value is None:
        return []
    return [value]


def _table(headers: Sequence[str], rows: Sequence[Sequence[str]]) -> str:
    if not rows:
        return "No results."

    widths = [
        max(len(header), *(len(row[index]) for row in rows))
        for index, header in enumerate(headers)
    ]
    rendered = [
        "  ".join(header.ljust(widths[index]) for index, header in enumerate(headers))
    ]
    rendered.append("  ".join("-" * width for width in widths))
    rendered.extend(
        "  ".join(value.ljust(widths[index]) for index, value in enumerate(row))
        for row in rows
    )
    return "\n".join(rendered)


def _print_json(value: Jsonable, *, fields: Sequence[str] = ()) -> None:
    payload = _filter_fields(_as_jsonable(value), fields)
    text = json.dumps(payload, indent=2, ensure_ascii=False)
    if typer is None:
        print(text)
        return
    typer.echo(text)


def _print_table(
    value: Jsonable,
    columns: Sequence[str],
    *,
    fields: Sequence[str] = (),
) -> None:
    selected_columns = fields or columns
    rows = [
        [_format_value(_get_path(item, column)) for column in selected_columns]
        for item in _items(value)
    ]
    headers = [column.replace(".", " ").title() for column in selected_columns]
    text = _table(headers, rows)
    if typer is None:
        print(text)
        return
    typer.echo(text)


def _print_success(value: str | None = None) -> None:
    if typer is None:
        print(value or "OK")
        return
    typer.echo(value or "OK")


async def _run(command: AsyncCommand, *, scopes: Sequence[str]) -> Jsonable:
    async with Spotifyify(scopes=_parse_scopes(scopes)) as spotify:
        return await command(spotify)


if typer is not None:
    app = typer.Typer(help="Command line tools for the spotifyify Spotify client.")
    tracks_app = typer.Typer(help="Work with Spotify tracks.")
    artists_app = typer.Typer(help="Work with Spotify artists.")
    albums_app = typer.Typer(help="Work with Spotify albums.")
    playlists_app = typer.Typer(help="Work with Spotify playlists.")
    shows_app = typer.Typer(help="Work with Spotify shows.")
    episodes_app = typer.Typer(help="Work with Spotify episodes.")
    library_app = typer.Typer(help="Work with the current user's library.")
    player_app = typer.Typer(help="Control and inspect Spotify playback.")
    users_app = typer.Typer(help="Work with Spotify users and following.")

    app.add_typer(tracks_app, name="tracks")
    app.add_typer(artists_app, name="artists")
    app.add_typer(albums_app, name="albums")
    app.add_typer(playlists_app, name="playlists")
    app.add_typer(shows_app, name="shows")
    app.add_typer(episodes_app, name="episodes")
    app.add_typer(library_app, name="library")
    app.add_typer(player_app, name="player")
    app.add_typer(users_app, name="users")

    ScopeOption = Annotated[
        list[str] | None,
        typer.Option(
            "--scope",
            "-s",
            help="OAuth scope. Can be repeated or comma-separated.",
        ),
    ]
    JsonOption = Annotated[
        bool,
        typer.Option("--json", help="Print JSON instead of a compact table."),
    ]
    FieldsOption = Annotated[
        list[str] | None,
        typer.Option(
            "--field",
            "--fields",
            "-f",
            help="Field path to include. Can be repeated or comma-separated.",
        ),
    ]
    LimitOption = Annotated[
        int,
        typer.Option("--limit", "-l", min=1, max=50, help="Number of items to fetch."),
    ]
    OffsetOption = Annotated[
        int,
        typer.Option("--offset", "-o", min=0, help="Result offset."),
    ]
    MarketOption = Annotated[
        str | None,
        typer.Option("--market", "-m", help="ISO 3166-1 alpha-2 market code."),
    ]
    DeviceOption = Annotated[
        str | None,
        typer.Option("--device-id", help="Spotify device ID."),
    ]
    IdsArgument = Annotated[
        list[str],
        typer.Argument(help="One or more IDs. Values can also be comma-separated."),
    ]
    UrisArgument = Annotated[
        list[str],
        typer.Argument(help="One or more Spotify URIs. Values can be comma-separated."),
    ]

    def _handle(command: AsyncCommand, *, scopes: Sequence[str]) -> Jsonable:
        try:
            return asyncio.run(_run(command, scopes=scopes))
        except (SpotifyAPIError, SpotifyAuthError) as exc:
            typer.echo(str(exc), err=True)
            raise typer.Exit(1) from exc

    def _render(
        result: Jsonable,
        *,
        json_output: bool,
        fields: Sequence[str] | None,
        columns: Sequence[str],
    ) -> None:
        selected_fields = _split_values(fields)
        if json_output:
            _print_json(result, fields=selected_fields)
            return
        _print_table(result, columns, fields=selected_fields)

    @tracks_app.command("search")
    def search_tracks(
        query: Annotated[str, typer.Argument(help="Spotify search query.")],
        limit: LimitOption = DEFAULT_LIMIT,
        offset: OffsetOption = 0,
        market: MarketOption = None,
        json_output: JsonOption = False,
        fields: FieldsOption = None,
        scope: ScopeOption = None,
    ) -> None:
        result = _handle(
            lambda spotify: spotify.tracks.find(
                query, limit=limit, offset=offset, market=market
            ),
            scopes=_coalesce_scopes(scope),
        )
        _render(
            result,
            json_output=json_output,
            fields=fields,
            columns=("id", "name", "artists", "album.name", "uri"),
        )

    @tracks_app.command("get")
    def get_track(
        track_id: Annotated[str, typer.Argument(help="Spotify track ID.")],
        market: MarketOption = None,
        json_output: JsonOption = False,
        fields: FieldsOption = None,
        scope: ScopeOption = None,
    ) -> None:
        result = _handle(
            lambda spotify: spotify.tracks.get(track_id, market=market),
            scopes=_coalesce_scopes(scope),
        )
        _render(
            result,
            json_output=json_output,
            fields=fields,
            columns=("id", "name", "artists", "album.name", "uri"),
        )

    @tracks_app.command("get-many")
    def get_many_tracks(
        track_ids: IdsArgument,
        market: MarketOption = None,
        json_output: JsonOption = False,
        fields: FieldsOption = None,
        scope: ScopeOption = None,
    ) -> None:
        result = _handle(
            lambda spotify: spotify.tracks.get_many(
                _split_values(track_ids), market=market
            ),
            scopes=_coalesce_scopes(scope),
        )
        _render(
            result,
            json_output=json_output,
            fields=fields,
            columns=("id", "name", "artists", "album.name", "uri"),
        )

    @tracks_app.command("audio-features")
    def audio_features(
        track_ids: IdsArgument,
        json_output: JsonOption = False,
        fields: FieldsOption = None,
        scope: ScopeOption = None,
    ) -> None:
        result = _handle(
            lambda spotify: spotify.tracks.audio_features(_split_values(track_ids)),
            scopes=_coalesce_scopes(scope),
        )
        _render(
            result,
            json_output=json_output,
            fields=fields,
            columns=("id", "danceability", "energy", "tempo", "valence"),
        )

    @tracks_app.command("recommendations")
    def recommendations(
        seed_artists: Annotated[
            list[str] | None,
            typer.Option("--seed-artist", help="Seed artist ID."),
        ] = None,
        seed_tracks: Annotated[
            list[str] | None,
            typer.Option("--seed-track", help="Seed track ID."),
        ] = None,
        seed_genres: Annotated[
            list[str] | None,
            typer.Option("--seed-genre", help="Seed genre."),
        ] = None,
        limit: LimitOption = 20,
        market: MarketOption = None,
        json_output: JsonOption = False,
        fields: FieldsOption = None,
        scope: ScopeOption = None,
    ) -> None:
        result = _handle(
            lambda spotify: spotify.tracks.recommendations(
                seed_artists=_split_values(seed_artists),
                seed_tracks=_split_values(seed_tracks),
                seed_genres=_split_values(seed_genres),
                limit=limit,
                market=market,
            ),
            scopes=_coalesce_scopes(scope),
        )
        tracks = result.tracks if not json_output and not fields else result
        _render(
            tracks,
            json_output=json_output,
            fields=fields,
            columns=("id", "name", "artists", "uri"),
        )

    @artists_app.command("search")
    def search_artists(
        query: Annotated[str, typer.Argument(help="Spotify search query.")],
        limit: LimitOption = DEFAULT_LIMIT,
        offset: OffsetOption = 0,
        json_output: JsonOption = False,
        fields: FieldsOption = None,
        scope: ScopeOption = None,
    ) -> None:
        result = _handle(
            lambda spotify: spotify.artists.find(query, limit=limit, offset=offset),
            scopes=_coalesce_scopes(scope),
        )
        _render(
            result,
            json_output=json_output,
            fields=fields,
            columns=("id", "name", "uri"),
        )

    @artists_app.command("get")
    def get_artist(
        artist_id: Annotated[str, typer.Argument(help="Spotify artist ID.")],
        json_output: JsonOption = False,
        fields: FieldsOption = None,
        scope: ScopeOption = None,
    ) -> None:
        result = _handle(
            lambda spotify: spotify.artists.get(artist_id),
            scopes=_coalesce_scopes(scope),
        )
        _render(
            result,
            json_output=json_output,
            fields=fields,
            columns=("id", "name", "uri"),
        )

    @artists_app.command("get-many")
    def get_many_artists(
        artist_ids: IdsArgument,
        json_output: JsonOption = False,
        fields: FieldsOption = None,
        scope: ScopeOption = None,
    ) -> None:
        result = _handle(
            lambda spotify: spotify.artists.get_many(_split_values(artist_ids)),
            scopes=_coalesce_scopes(scope),
        )
        _render(
            result,
            json_output=json_output,
            fields=fields,
            columns=("id", "name", "uri"),
        )

    @artists_app.command("top-tracks")
    def artist_top_tracks(
        artist_id: Annotated[str, typer.Argument(help="Spotify artist ID.")],
        market: Annotated[str, typer.Option("--market", "-m")] = "US",
        json_output: JsonOption = False,
        fields: FieldsOption = None,
        scope: ScopeOption = None,
    ) -> None:
        result = _handle(
            lambda spotify: spotify.artists.top_tracks(artist_id, market=market),
            scopes=_coalesce_scopes(scope),
        )
        _render(
            result,
            json_output=json_output,
            fields=fields,
            columns=("id", "name", "artists", "uri"),
        )

    @artists_app.command("albums")
    def artist_albums(
        artist_id: Annotated[str, typer.Argument(help="Spotify artist ID.")],
        include_groups: Annotated[
            str | None,
            typer.Option(
                "--include-groups", help="album,single,appears_on,compilation"
            ),
        ] = None,
        market: MarketOption = None,
        limit: LimitOption = 20,
        offset: OffsetOption = 0,
        json_output: JsonOption = False,
        fields: FieldsOption = None,
        scope: ScopeOption = None,
    ) -> None:
        result = _handle(
            lambda spotify: spotify.artists.albums(
                artist_id,
                include_groups=include_groups,
                market=market,
                limit=limit,
                offset=offset,
            ),
            scopes=_coalesce_scopes(scope),
        )
        _render(
            result,
            json_output=json_output,
            fields=fields,
            columns=("id", "name", "album_type", "uri"),
        )

    @artists_app.command("related")
    def related_artists(
        artist_id: Annotated[str, typer.Argument(help="Spotify artist ID.")],
        json_output: JsonOption = False,
        fields: FieldsOption = None,
        scope: ScopeOption = None,
    ) -> None:
        result = _handle(
            lambda spotify: spotify.artists.related(artist_id),
            scopes=_coalesce_scopes(scope),
        )
        _render(
            result,
            json_output=json_output,
            fields=fields,
            columns=("id", "name", "uri"),
        )

    @albums_app.command("search")
    def search_albums(
        query: Annotated[str, typer.Argument(help="Spotify search query.")],
        limit: LimitOption = DEFAULT_LIMIT,
        offset: OffsetOption = 0,
        market: MarketOption = None,
        json_output: JsonOption = False,
        fields: FieldsOption = None,
        scope: ScopeOption = None,
    ) -> None:
        result = _handle(
            lambda spotify: spotify.albums.find(
                query, limit=limit, offset=offset, market=market
            ),
            scopes=_coalesce_scopes(scope),
        )
        _render(
            result,
            json_output=json_output,
            fields=fields,
            columns=("id", "name", "artists", "uri"),
        )

    @albums_app.command("get")
    def get_album(
        album_id: Annotated[str, typer.Argument(help="Spotify album ID.")],
        market: MarketOption = None,
        json_output: JsonOption = False,
        fields: FieldsOption = None,
        scope: ScopeOption = None,
    ) -> None:
        result = _handle(
            lambda spotify: spotify.albums.get(album_id, market=market),
            scopes=_coalesce_scopes(scope),
        )
        _render(
            result,
            json_output=json_output,
            fields=fields,
            columns=("id", "name", "artists", "uri"),
        )

    @albums_app.command("get-many")
    def get_many_albums(
        album_ids: IdsArgument,
        market: MarketOption = None,
        json_output: JsonOption = False,
        fields: FieldsOption = None,
        scope: ScopeOption = None,
    ) -> None:
        result = _handle(
            lambda spotify: spotify.albums.get_many(
                _split_values(album_ids), market=market
            ),
            scopes=_coalesce_scopes(scope),
        )
        _render(
            result,
            json_output=json_output,
            fields=fields,
            columns=("id", "name", "artists", "uri"),
        )

    @albums_app.command("tracks")
    def album_tracks(
        album_id: Annotated[str, typer.Argument(help="Spotify album ID.")],
        limit: LimitOption = 50,
        offset: OffsetOption = 0,
        market: MarketOption = None,
        json_output: JsonOption = False,
        fields: FieldsOption = None,
        scope: ScopeOption = None,
    ) -> None:
        result = _handle(
            lambda spotify: spotify.albums.tracks(
                album_id, limit=limit, offset=offset, market=market
            ),
            scopes=_coalesce_scopes(scope),
        )
        _render(
            result,
            json_output=json_output,
            fields=fields,
            columns=("id", "name", "artists", "uri"),
        )

    @albums_app.command("new-releases")
    def new_releases(
        country: Annotated[str | None, typer.Option("--country", "-c")] = None,
        limit: LimitOption = 20,
        offset: OffsetOption = 0,
        json_output: JsonOption = False,
        fields: FieldsOption = None,
        scope: ScopeOption = None,
    ) -> None:
        result = _handle(
            lambda spotify: spotify.albums.new_releases(
                country=country, limit=limit, offset=offset
            ),
            scopes=_coalesce_scopes(scope),
        )
        _render(
            result,
            json_output=json_output,
            fields=fields,
            columns=("id", "name", "artists", "uri"),
        )

    @playlists_app.command("search")
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

    @playlists_app.command("get")
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

    @playlists_app.command("list")
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
            scopes=_coalesce_scopes(scope)
            or [SpotifyScope.PLAYLIST_READ_PRIVATE.value],
        )
        _render(
            result,
            json_output=json_output,
            fields=fields,
            columns=("id", "name", "owner", "uri"),
        )

    @playlists_app.command("tracks")
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

    @playlists_app.command("create")
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
            scopes=_coalesce_scopes(scope)
            or [
                SpotifyScope.PLAYLIST_MODIFY_PUBLIC.value,
                SpotifyScope.PLAYLIST_MODIFY_PRIVATE.value,
            ],
        )
        _render(
            result,
            json_output=json_output,
            fields=fields,
            columns=("id", "name", "uri"),
        )

    @playlists_app.command("update")
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
            scopes=_coalesce_scopes(scope)
            or [
                SpotifyScope.PLAYLIST_MODIFY_PUBLIC.value,
                SpotifyScope.PLAYLIST_MODIFY_PRIVATE.value,
            ],
        )
        _print_success()

    @playlists_app.command("add")
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
            scopes=_coalesce_scopes(scope)
            or [
                SpotifyScope.PLAYLIST_MODIFY_PUBLIC.value,
                SpotifyScope.PLAYLIST_MODIFY_PRIVATE.value,
            ],
        )
        payload = {"snapshot_id": result}
        (
            _print_json(payload, fields=_split_values(fields))
            if json_output
            else _print_success(result)
        )

    @playlists_app.command("replace")
    def replace_playlist_items(
        playlist_id: Annotated[str, typer.Argument(help="Spotify playlist ID.")],
        uris: UrisArgument,
        json_output: JsonOption = False,
        fields: FieldsOption = None,
        scope: ScopeOption = None,
    ) -> None:
        result = _handle(
            lambda spotify: spotify.playlists.replace(playlist_id, _split_values(uris)),
            scopes=_coalesce_scopes(scope)
            or [
                SpotifyScope.PLAYLIST_MODIFY_PUBLIC.value,
                SpotifyScope.PLAYLIST_MODIFY_PRIVATE.value,
            ],
        )
        payload = {"snapshot_id": result}
        (
            _print_json(payload, fields=_split_values(fields))
            if json_output
            else _print_success(result)
        )

    @playlists_app.command("remove")
    def remove_playlist_items(
        playlist_id: Annotated[str, typer.Argument(help="Spotify playlist ID.")],
        uris: UrisArgument,
        json_output: JsonOption = False,
        fields: FieldsOption = None,
        scope: ScopeOption = None,
    ) -> None:
        result = _handle(
            lambda spotify: spotify.playlists.remove(playlist_id, _split_values(uris)),
            scopes=_coalesce_scopes(scope)
            or [
                SpotifyScope.PLAYLIST_MODIFY_PUBLIC.value,
                SpotifyScope.PLAYLIST_MODIFY_PRIVATE.value,
            ],
        )
        payload = {"snapshot_id": result}
        (
            _print_json(payload, fields=_split_values(fields))
            if json_output
            else _print_success(result)
        )

    @playlists_app.command("reorder")
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
            scopes=_coalesce_scopes(scope)
            or [
                SpotifyScope.PLAYLIST_MODIFY_PUBLIC.value,
                SpotifyScope.PLAYLIST_MODIFY_PRIVATE.value,
            ],
        )
        payload = {"snapshot_id": result}
        (
            _print_json(payload, fields=_split_values(fields))
            if json_output
            else _print_success(result)
        )

    @playlists_app.command("cover-image")
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

    @shows_app.command("search")
    def search_shows(
        query: Annotated[str, typer.Argument(help="Spotify search query.")],
        limit: LimitOption = DEFAULT_LIMIT,
        offset: OffsetOption = 0,
        market: MarketOption = None,
        json_output: JsonOption = False,
        fields: FieldsOption = None,
        scope: ScopeOption = None,
    ) -> None:
        result = _handle(
            lambda spotify: spotify.shows.find(
                query, limit=limit, offset=offset, market=market
            ),
            scopes=_coalesce_scopes(scope),
        )
        _render(
            result,
            json_output=json_output,
            fields=fields,
            columns=("id", "name", "publisher", "uri"),
        )

    @shows_app.command("get")
    def get_show(
        show_id: Annotated[str, typer.Argument(help="Spotify show ID.")],
        market: MarketOption = None,
        json_output: JsonOption = False,
        fields: FieldsOption = None,
        scope: ScopeOption = None,
    ) -> None:
        result = _handle(
            lambda spotify: spotify.shows.get(show_id, market=market),
            scopes=_coalesce_scopes(scope),
        )
        _render(
            result,
            json_output=json_output,
            fields=fields,
            columns=("id", "name", "publisher", "uri"),
        )

    @shows_app.command("get-many")
    def get_many_shows(
        show_ids: IdsArgument,
        market: MarketOption = None,
        json_output: JsonOption = False,
        fields: FieldsOption = None,
        scope: ScopeOption = None,
    ) -> None:
        result = _handle(
            lambda spotify: spotify.shows.get_many(
                _split_values(show_ids), market=market
            ),
            scopes=_coalesce_scopes(scope),
        )
        _render(
            result,
            json_output=json_output,
            fields=fields,
            columns=("id", "name", "publisher", "uri"),
        )

    @shows_app.command("episodes")
    def show_episodes(
        show_id: Annotated[str, typer.Argument(help="Spotify show ID.")],
        market: MarketOption = None,
        limit: LimitOption = 20,
        offset: OffsetOption = 0,
        json_output: JsonOption = False,
        fields: FieldsOption = None,
        scope: ScopeOption = None,
    ) -> None:
        result = _handle(
            lambda spotify: spotify.shows.episodes(
                show_id, market=market, limit=limit, offset=offset
            ),
            scopes=_coalesce_scopes(scope),
        )
        _render(
            result,
            json_output=json_output,
            fields=fields,
            columns=("id", "name", "release_date", "uri"),
        )

    @episodes_app.command("search")
    def search_episodes(
        query: Annotated[str, typer.Argument(help="Spotify search query.")],
        limit: LimitOption = DEFAULT_LIMIT,
        offset: OffsetOption = 0,
        market: MarketOption = None,
        json_output: JsonOption = False,
        fields: FieldsOption = None,
        scope: ScopeOption = None,
    ) -> None:
        result = _handle(
            lambda spotify: spotify.episodes.find(
                query, limit=limit, offset=offset, market=market
            ),
            scopes=_coalesce_scopes(scope),
        )
        _render(
            result,
            json_output=json_output,
            fields=fields,
            columns=("id", "name", "release_date", "uri"),
        )

    @episodes_app.command("get")
    def get_episode(
        episode_id: Annotated[str, typer.Argument(help="Spotify episode ID.")],
        market: MarketOption = None,
        json_output: JsonOption = False,
        fields: FieldsOption = None,
        scope: ScopeOption = None,
    ) -> None:
        result = _handle(
            lambda spotify: spotify.episodes.get(episode_id, market=market),
            scopes=_coalesce_scopes(scope),
        )
        _render(
            result,
            json_output=json_output,
            fields=fields,
            columns=("id", "name", "show.name", "uri"),
        )

    @episodes_app.command("get-many")
    def get_many_episodes(
        episode_ids: IdsArgument,
        market: MarketOption = None,
        json_output: JsonOption = False,
        fields: FieldsOption = None,
        scope: ScopeOption = None,
    ) -> None:
        result = _handle(
            lambda spotify: spotify.episodes.get_many(
                _split_values(episode_ids), market=market
            ),
            scopes=_coalesce_scopes(scope),
        )
        _render(
            result,
            json_output=json_output,
            fields=fields,
            columns=("id", "name", "show.name", "uri"),
        )

    def _saved_scope(scope: Sequence[str] | None) -> Sequence[str]:
        return _coalesce_scopes(scope) or [SpotifyScope.USER_LIBRARY_READ.value]

    def _modify_library_scope(scope: Sequence[str] | None) -> Sequence[str]:
        return _coalesce_scopes(scope) or [SpotifyScope.USER_LIBRARY_MODIFY.value]

    @library_app.command("saved-tracks")
    def saved_tracks(
        limit: LimitOption = 20,
        offset: OffsetOption = 0,
        market: MarketOption = None,
        json_output: JsonOption = False,
        fields: FieldsOption = None,
        scope: ScopeOption = None,
    ) -> None:
        result = _handle(
            lambda spotify: spotify.library.saved_tracks(
                limit=limit, offset=offset, market=market
            ),
            scopes=_saved_scope(scope),
        )
        _render(
            result,
            json_output=json_output,
            fields=fields,
            columns=("track.id", "track.name", "track.artists", "added_at"),
        )

    @library_app.command("saved-albums")
    def saved_albums(
        limit: LimitOption = 20,
        offset: OffsetOption = 0,
        market: MarketOption = None,
        json_output: JsonOption = False,
        fields: FieldsOption = None,
        scope: ScopeOption = None,
    ) -> None:
        result = _handle(
            lambda spotify: spotify.library.saved_albums(
                limit=limit, offset=offset, market=market
            ),
            scopes=_saved_scope(scope),
        )
        _render(
            result,
            json_output=json_output,
            fields=fields,
            columns=("album.id", "album.name", "album.artists", "added_at"),
        )

    @library_app.command("saved-shows")
    def saved_shows(
        limit: LimitOption = 20,
        offset: OffsetOption = 0,
        json_output: JsonOption = False,
        fields: FieldsOption = None,
        scope: ScopeOption = None,
    ) -> None:
        result = _handle(
            lambda spotify: spotify.library.saved_shows(limit=limit, offset=offset),
            scopes=_saved_scope(scope),
        )
        _render(
            result,
            json_output=json_output,
            fields=fields,
            columns=("show.id", "show.name", "show.publisher", "added_at"),
        )

    @library_app.command("saved-episodes")
    def saved_episodes(
        limit: LimitOption = 20,
        offset: OffsetOption = 0,
        json_output: JsonOption = False,
        fields: FieldsOption = None,
        scope: ScopeOption = None,
    ) -> None:
        result = _handle(
            lambda spotify: spotify.library.saved_episodes(limit=limit, offset=offset),
            scopes=_saved_scope(scope),
        )
        _render(
            result,
            json_output=json_output,
            fields=fields,
            columns=("episode.id", "episode.name", "added_at"),
        )

    @library_app.command("top-tracks")
    def library_top_tracks(
        time_range: Annotated[str, typer.Option("--time-range")] = "medium_term",
        limit: LimitOption = 20,
        offset: OffsetOption = 0,
        json_output: JsonOption = False,
        fields: FieldsOption = None,
        scope: ScopeOption = None,
    ) -> None:
        result = _handle(
            lambda spotify: spotify.library.top_tracks(
                time_range=time_range, limit=limit, offset=offset
            ),
            scopes=_coalesce_scopes(scope) or [SpotifyScope.USER_TOP_READ.value],
        )
        _render(
            result,
            json_output=json_output,
            fields=fields,
            columns=("id", "name", "artists", "uri"),
        )

    @library_app.command("top-artists")
    def library_top_artists(
        time_range: Annotated[str, typer.Option("--time-range")] = "medium_term",
        limit: LimitOption = 20,
        offset: OffsetOption = 0,
        json_output: JsonOption = False,
        fields: FieldsOption = None,
        scope: ScopeOption = None,
    ) -> None:
        result = _handle(
            lambda spotify: spotify.library.top_artists(
                time_range=time_range, limit=limit, offset=offset
            ),
            scopes=_coalesce_scopes(scope) or [SpotifyScope.USER_TOP_READ.value],
        )
        _render(
            result,
            json_output=json_output,
            fields=fields,
            columns=("id", "name", "uri"),
        )

    def _library_action(
        ids: Sequence[str],
        *,
        action: Callable[[Spotifyify, list[str]], Awaitable[Jsonable]],
        scope: Sequence[str] | None,
    ) -> None:
        _handle(
            lambda spotify: action(spotify, _split_values(ids)),
            scopes=_modify_library_scope(scope),
        )
        _print_success()

    def _library_check(
        ids: Sequence[str],
        *,
        action: Callable[[Spotifyify, list[str]], Awaitable[list[bool]]],
        scope: Sequence[str] | None,
        json_output: bool,
    ) -> None:
        item_ids = _split_values(ids)
        result = _handle(
            lambda spotify: action(spotify, item_ids), scopes=_saved_scope(scope)
        )
        payload = [
            {"id": item_id, "saved": saved}
            for item_id, saved in zip(item_ids, result, strict=False)
        ]
        _print_json(payload) if json_output else _print_table(payload, ("id", "saved"))

    @library_app.command("save-tracks")
    def save_tracks(track_ids: IdsArgument, scope: ScopeOption = None) -> None:
        _library_action(
            track_ids,
            action=lambda spotify, ids: spotify.library.save_tracks(ids),
            scope=scope,
        )

    @library_app.command("remove-tracks")
    def remove_tracks(track_ids: IdsArgument, scope: ScopeOption = None) -> None:
        _library_action(
            track_ids,
            action=lambda spotify, ids: spotify.library.remove_tracks(ids),
            scope=scope,
        )

    @library_app.command("check-tracks")
    def check_tracks(
        track_ids: IdsArgument,
        json_output: JsonOption = False,
        scope: ScopeOption = None,
    ) -> None:
        _library_check(
            track_ids,
            action=lambda spotify, ids: spotify.library.check_tracks(ids),
            scope=scope,
            json_output=json_output,
        )

    @library_app.command("save-albums")
    def save_albums(album_ids: IdsArgument, scope: ScopeOption = None) -> None:
        _library_action(
            album_ids,
            action=lambda spotify, ids: spotify.library.save_albums(ids),
            scope=scope,
        )

    @library_app.command("remove-albums")
    def remove_albums(album_ids: IdsArgument, scope: ScopeOption = None) -> None:
        _library_action(
            album_ids,
            action=lambda spotify, ids: spotify.library.remove_albums(ids),
            scope=scope,
        )

    @library_app.command("check-albums")
    def check_albums(
        album_ids: IdsArgument,
        json_output: JsonOption = False,
        scope: ScopeOption = None,
    ) -> None:
        _library_check(
            album_ids,
            action=lambda spotify, ids: spotify.library.check_albums(ids),
            scope=scope,
            json_output=json_output,
        )

    @library_app.command("save-shows")
    def save_shows(show_ids: IdsArgument, scope: ScopeOption = None) -> None:
        _library_action(
            show_ids,
            action=lambda spotify, ids: spotify.library.save_shows(ids),
            scope=scope,
        )

    @library_app.command("remove-shows")
    def remove_shows(show_ids: IdsArgument, scope: ScopeOption = None) -> None:
        _library_action(
            show_ids,
            action=lambda spotify, ids: spotify.library.remove_shows(ids),
            scope=scope,
        )

    @library_app.command("check-shows")
    def check_shows(
        show_ids: IdsArgument,
        json_output: JsonOption = False,
        scope: ScopeOption = None,
    ) -> None:
        _library_check(
            show_ids,
            action=lambda spotify, ids: spotify.library.check_shows(ids),
            scope=scope,
            json_output=json_output,
        )

    @library_app.command("save-episodes")
    def save_episodes(episode_ids: IdsArgument, scope: ScopeOption = None) -> None:
        _library_action(
            episode_ids,
            action=lambda spotify, ids: spotify.library.save_episodes(ids),
            scope=scope,
        )

    @library_app.command("remove-episodes")
    def remove_episodes(episode_ids: IdsArgument, scope: ScopeOption = None) -> None:
        _library_action(
            episode_ids,
            action=lambda spotify, ids: spotify.library.remove_episodes(ids),
            scope=scope,
        )

    @library_app.command("check-episodes")
    def check_episodes(
        episode_ids: IdsArgument,
        json_output: JsonOption = False,
        scope: ScopeOption = None,
    ) -> None:
        _library_check(
            episode_ids,
            action=lambda spotify, ids: spotify.library.check_episodes(ids),
            scope=scope,
            json_output=json_output,
        )

    @player_app.command("state")
    def player_state(
        market: MarketOption = None,
        json_output: JsonOption = False,
        fields: FieldsOption = None,
        scope: ScopeOption = None,
    ) -> None:
        result = _handle(
            lambda spotify: spotify.player.state(market=market),
            scopes=_coalesce_scopes(scope)
            or [SpotifyScope.USER_READ_PLAYBACK_STATE.value],
        )
        _render(
            result,
            json_output=json_output,
            fields=fields,
            columns=("item.id", "item.name", "is_playing", "progress_ms"),
        )

    @player_app.command("play")
    def player_play(
        device_id: DeviceOption = None,
        context_uri: Annotated[str | None, typer.Option("--context-uri")] = None,
        uri: Annotated[list[str] | None, typer.Option("--uri")] = None,
        offset: Annotated[str | None, typer.Option("--offset-json")] = None,
        position_ms: Annotated[int | None, typer.Option("--position-ms", min=0)] = None,
        scope: ScopeOption = None,
    ) -> None:
        _handle(
            lambda spotify: spotify.player.play(
                device_id=device_id,
                context_uri=context_uri,
                uris=_split_values(uri) or None,
                offset=_parse_json_object(offset, "--offset-json"),
                position_ms=position_ms,
            ),
            scopes=_coalesce_scopes(scope)
            or [SpotifyScope.USER_MODIFY_PLAYBACK_STATE.value],
        )
        _print_success()

    @player_app.command("pause")
    def player_pause(device_id: DeviceOption = None, scope: ScopeOption = None) -> None:
        _handle(
            lambda spotify: spotify.player.pause(device_id=device_id),
            scopes=_coalesce_scopes(scope)
            or [SpotifyScope.USER_MODIFY_PLAYBACK_STATE.value],
        )
        _print_success()

    @player_app.command("skip")
    def player_skip(device_id: DeviceOption = None, scope: ScopeOption = None) -> None:
        _handle(
            lambda spotify: spotify.player.skip(device_id=device_id),
            scopes=_coalesce_scopes(scope)
            or [SpotifyScope.USER_MODIFY_PLAYBACK_STATE.value],
        )
        _print_success()

    @player_app.command("previous")
    def player_previous(
        device_id: DeviceOption = None, scope: ScopeOption = None
    ) -> None:
        _handle(
            lambda spotify: spotify.player.previous(device_id=device_id),
            scopes=_coalesce_scopes(scope)
            or [SpotifyScope.USER_MODIFY_PLAYBACK_STATE.value],
        )
        _print_success()

    @player_app.command("seek")
    def player_seek(
        position_ms: Annotated[int, typer.Argument(min=0)],
        device_id: DeviceOption = None,
        scope: ScopeOption = None,
    ) -> None:
        _handle(
            lambda spotify: spotify.player.seek(position_ms, device_id=device_id),
            scopes=_coalesce_scopes(scope)
            or [SpotifyScope.USER_MODIFY_PLAYBACK_STATE.value],
        )
        _print_success()

    @player_app.command("repeat")
    def player_repeat(
        state: Annotated[str, typer.Argument(help="track, context, or off")],
        device_id: DeviceOption = None,
        scope: ScopeOption = None,
    ) -> None:
        _handle(
            lambda spotify: spotify.player.repeat(state, device_id=device_id),
            scopes=_coalesce_scopes(scope)
            or [SpotifyScope.USER_MODIFY_PLAYBACK_STATE.value],
        )
        _print_success()

    @player_app.command("shuffle")
    def player_shuffle(
        state: Annotated[bool, typer.Argument()],
        device_id: DeviceOption = None,
        scope: ScopeOption = None,
    ) -> None:
        _handle(
            lambda spotify: spotify.player.shuffle(state, device_id=device_id),
            scopes=_coalesce_scopes(scope)
            or [SpotifyScope.USER_MODIFY_PLAYBACK_STATE.value],
        )
        _print_success()

    @player_app.command("volume")
    def player_volume(
        volume_percent: Annotated[int, typer.Argument(min=0, max=100)],
        device_id: DeviceOption = None,
        scope: ScopeOption = None,
    ) -> None:
        _handle(
            lambda spotify: spotify.player.volume(volume_percent, device_id=device_id),
            scopes=_coalesce_scopes(scope)
            or [SpotifyScope.USER_MODIFY_PLAYBACK_STATE.value],
        )
        _print_success()

    @player_app.command("queue")
    def player_queue(
        json_output: JsonOption = False,
        fields: FieldsOption = None,
        scope: ScopeOption = None,
    ) -> None:
        result = _handle(
            lambda spotify: spotify.player.queue(),
            scopes=_coalesce_scopes(scope)
            or [SpotifyScope.USER_READ_PLAYBACK_STATE.value],
        )
        _render(
            result,
            json_output=json_output,
            fields=fields,
            columns=("id", "name", "artists", "uri"),
        )

    @player_app.command("add-to-queue")
    def add_to_queue(
        uri: Annotated[str, typer.Argument(help="Track or episode URI.")],
        device_id: DeviceOption = None,
        scope: ScopeOption = None,
    ) -> None:
        _handle(
            lambda spotify: spotify.player.add_to_queue(uri, device_id=device_id),
            scopes=_coalesce_scopes(scope)
            or [SpotifyScope.USER_MODIFY_PLAYBACK_STATE.value],
        )
        _print_success()

    @player_app.command("transfer")
    def transfer_playback(
        device_id: Annotated[str, typer.Argument(help="Spotify device ID.")],
        play: Annotated[bool, typer.Option("--play/--no-play")] = False,
        scope: ScopeOption = None,
    ) -> None:
        _handle(
            lambda spotify: spotify.player.transfer(device_id, play=play),
            scopes=_coalesce_scopes(scope)
            or [SpotifyScope.USER_MODIFY_PLAYBACK_STATE.value],
        )
        _print_success()

    @player_app.command("devices")
    def player_devices(
        json_output: JsonOption = False,
        fields: FieldsOption = None,
        scope: ScopeOption = None,
    ) -> None:
        result = _handle(
            lambda spotify: spotify.player.devices(),
            scopes=_coalesce_scopes(scope)
            or [SpotifyScope.USER_READ_PLAYBACK_STATE.value],
        )
        _render(
            result,
            json_output=json_output,
            fields=fields,
            columns=("id", "name", "type", "is_active", "volume_percent"),
        )

    @player_app.command("recently-played")
    def recently_played(
        limit: LimitOption = 20,
        after: Annotated[int | None, typer.Option("--after")] = None,
        before: Annotated[int | None, typer.Option("--before")] = None,
        json_output: JsonOption = False,
        fields: FieldsOption = None,
        scope: ScopeOption = None,
    ) -> None:
        result = _handle(
            lambda spotify: spotify.player.recently_played(
                limit=limit, after=after, before=before
            ),
            scopes=_coalesce_scopes(scope)
            or [SpotifyScope.USER_READ_RECENTLY_PLAYED.value],
        )
        _render(
            result,
            json_output=json_output,
            fields=fields,
            columns=("track.id", "track.name", "played_at"),
        )

    @users_app.command("me")
    def users_me(
        json_output: JsonOption = False,
        fields: FieldsOption = None,
        scope: ScopeOption = None,
    ) -> None:
        result = _handle(
            lambda spotify: spotify.users.me(), scopes=_coalesce_scopes(scope)
        )
        _render(
            result,
            json_output=json_output,
            fields=fields,
            columns=("id", "display_name", "uri"),
        )

    @users_app.command("get")
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

    @users_app.command("following")
    def users_following(
        type: Annotated[str, typer.Option("--type")] = "artist",
        limit: LimitOption = 20,
        after: Annotated[str | None, typer.Option("--after")] = None,
        json_output: JsonOption = False,
        fields: FieldsOption = None,
        scope: ScopeOption = None,
    ) -> None:
        result = _handle(
            lambda spotify: spotify.users.following(
                type=type, limit=limit, after=after
            ),
            scopes=_coalesce_scopes(scope) or [SpotifyScope.USER_LIBRARY_READ.value],
        )
        _render(
            result,
            json_output=json_output,
            fields=fields,
            columns=("id", "name", "uri"),
        )

    @users_app.command("follow")
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

    @users_app.command("unfollow")
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

    @users_app.command("check-following")
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


if __name__ == "__main__":
    main()
