from __future__ import annotations

import asyncio
from collections.abc import Sequence
from typing import Annotated

import typer

from spotifyify import SpotifyAPIError, SpotifyAuthError

from ._core import (
    AsyncCommand,
    Jsonable,
    _print_json,
    _print_table,
    _run,
    _split_values,
)

DEFAULT_LIMIT = 10

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
