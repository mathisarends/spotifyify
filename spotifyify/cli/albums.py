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

app = typer.Typer(help="Work with Spotify albums.")


@app.command("search")
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


@app.command("get")
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


@app.command("get-many")
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


@app.command("tracks")
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


@app.command("new-releases")
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
