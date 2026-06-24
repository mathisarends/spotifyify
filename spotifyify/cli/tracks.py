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

app = typer.Typer(help="Work with Spotify tracks.")


@app.command("search")
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


@app.command("get")
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


@app.command("get-many")
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


@app.command("audio-features")
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


@app.command("recommendations")
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
