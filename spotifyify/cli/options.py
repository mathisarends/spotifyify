import asyncio
from collections.abc import Sequence
from functools import wraps
from typing import Annotated, Any, Callable, ParamSpec
from collections.abc import Awaitable

import typer

from spotifyify import SpotifyAPIError, SpotifyAuthError

from spotifyify.cli.core import (
    Jsonable,
    as_jsonable,
    is_raw_output,
    print_json,
    rows,
    split_values,
)

DEFAULT_LIMIT = 10

EXIT_API_ERROR = 1
EXIT_AUTH_ERROR = 3

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
    fields: Sequence[str] | None = None,
    project: Callable[[Any], Any] | None = None,
) -> None:
    """Emit the command's declared columns, in order, as JSON.

    SPOTIFYIFY_RAW=1 opts out into the untouched Spotify payload, for
    debugging fields that are not part of any command's declared columns.
    """
    if is_raw_output():
        print_json(as_jsonable(result))
        return
    payload = project(result) if project is not None else result
    selected_columns = split_values(fields) or list(columns)
    print_json(rows(payload, selected_columns))
