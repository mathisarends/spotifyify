from __future__ import annotations

import asyncio
from collections.abc import Sequence
from functools import wraps
from typing import Annotated, Any, Callable, ParamSpec
from collections.abc import Awaitable

import typer

from spotifyify import SpotifyAPIError, SpotifyAuthError

from ._core import (
    FORMAT_JSON,
    FORMATS,
    Jsonable,
    _as_jsonable,
    _apply_sort,
    _apply_where,
    _print_json,
    _print_table,
    _resolve_format,
    _rows,
    _split_values,
)

DEFAULT_LIMIT = 10

EXIT_API_ERROR = 1
EXIT_AUTH_ERROR = 3

ScopeOption = Annotated[
    list[str] | None,
    typer.Option(
        "--scope",
        "-s",
        help="OAuth scope. Can be repeated or comma-separated.",
    ),
]
FormatOption = Annotated[
    str | None,
    typer.Option(
        "--format",
        help=f"Output format: {'|'.join(FORMATS)}. Defaults to json.",
    ),
]
JsonOption = Annotated[
    bool,
    typer.Option("--json", help="Shorthand for --format json."),
]
RawOption = Annotated[
    bool,
    typer.Option(
        "--raw",
        help="Emit the untouched Spotify payload instead of the declared columns.",
    ),
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
SortOption = Annotated[
    list[str] | None,
    typer.Option(
        "--sort",
        help="Field path to sort by; prefix with '-' for descending. Stable, repeatable.",
    ),
]
WhereOption = Annotated[
    list[str] | None,
    typer.Option(
        "--where",
        help="Keep rows where PATH contains VALUE (case-insensitive). Repeatable, AND-ed.",
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
WaitOption = Annotated[
    bool,
    typer.Option(
        "--wait/--no-wait",
        help="Wait for playback to reflect the change before reporting state.",
    ),
]
IdsArgument = Annotated[
    list[str],
    typer.Argument(help="One or more IDs. Values can also be comma-separated."),
]
UrisArgument = Annotated[
    list[str],
    typer.Argument(help="One or more Spotify URIs. Values can be comma-separated."),
]


P = ParamSpec("P")


def async_command(command: Callable[P, Awaitable[None]]) -> Callable[P, None]:
    """Bridge one async command into Typer and translate expected API failures."""

    @wraps(command)
    def run(*args: P.args, **kwargs: P.kwargs) -> None:
        try:
            asyncio.run(command(*args, **kwargs))
        except SpotifyAuthError as exc:
            typer.echo(str(exc), err=True)
            raise typer.Exit(EXIT_AUTH_ERROR) from exc
        except SpotifyAPIError as exc:
            typer.echo(str(exc), err=True)
            raise typer.Exit(EXIT_API_ERROR) from exc

    return run


def print_result(
    result: Jsonable,
    *,
    columns: Sequence[str],
    fmt: str | None = None,
    json_output: bool = False,
    raw: bool = False,
    fields: Sequence[str] | None = None,
    sort: Sequence[str] | None = None,
    where: Sequence[str] | None = None,
    project: Callable[[Any], Any] | None = None,
) -> None:
    """Emit the command's declared columns, in order, in the chosen format.

    Both formats project the same fixed set of fields, so switching format
    changes the encoding and nothing else. --raw opts out into the untouched
    Spotify payload.
    """
    if raw:
        _print_json(_as_jsonable(result))
        return
    payload = project(result) if project is not None else result
    payload = _apply_sort(_apply_where(payload, where), _split_values(sort))
    selected_columns = _split_values(fields) or list(columns)
    rows = _rows(payload, selected_columns)
    if _resolve_format(fmt, json_output=json_output) == FORMAT_JSON:
        _print_json(rows)
        return
    _print_table(rows, selected_columns)
