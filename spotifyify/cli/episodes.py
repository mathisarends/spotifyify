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

app = typer.Typer(help="Work with Spotify episodes.")


@app.command("search")
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


@app.command("get")
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


@app.command("get-many")
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
