from __future__ import annotations

from typing import Annotated

import typer

from ._core import _coalesce_scopes, _split_values
from ._options import (
    DEFAULT_LIMIT,
    FieldsOption,
    IdsArgument,
    JsonOption,
    LimitOption,
    MarketOption,
    OffsetOption,
    ScopeOption,
    _handle,
    _render,
)

app = typer.Typer(help="Work with Spotify artists.")


@app.command("search")
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


@app.command("get")
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


@app.command("get-many")
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


@app.command("top-tracks")
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


@app.command("albums")
def artist_albums(
    artist_id: Annotated[str, typer.Argument(help="Spotify artist ID.")],
    include_groups: Annotated[
        str | None,
        typer.Option("--include-groups", help="album,single,appears_on,compilation"),
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


@app.command("related")
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
