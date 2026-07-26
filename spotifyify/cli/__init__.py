from __future__ import annotations

import sys
from typing import Annotated

try:
    import typer
except ImportError:  # pragma: no cover - exercised by installed package users.
    typer = None

from ._core import (
    FORMATS,
    INSTALL_MESSAGE,
    _apply_sort,
    _apply_where,
    _cell,
    _filter_fields,
    _get_path,
    _parse_scopes,
    _playback_summary,
    _resolve_format,
    _rows,
    _sort_items,
    _split_values,
    _table,
)

__all__ = [
    "FORMATS",
    "INSTALL_MESSAGE",
    "main",
    "typer",
    "_apply_sort",
    "_apply_where",
    "_cell",
    "_filter_fields",
    "_get_path",
    "_parse_scopes",
    "_playback_summary",
    "_resolve_format",
    "_rows",
    "_sort_items",
    "_split_values",
    "_table",
]


def _force_utf8() -> None:
    """Emit UTF-8 whatever the console codepage is.

    On Windows stdout otherwise defaults to the ANSI codepage, so a captured or
    redirected result would not be valid UTF-8.
    """
    for stream in (sys.stdout, sys.stderr):
        reconfigure = getattr(stream, "reconfigure", None)
        if reconfigure is not None:
            reconfigure(encoding="utf-8", errors="replace")


def main() -> None:
    if typer is None:
        raise SystemExit(INSTALL_MESSAGE)
    _force_utf8()
    app()


if typer is not None:
    from . import (
        albums,
        artists,
        episodes,
        library,
        player,
        playlists,
        quick,
        shows,
        tracks,
        users,
    )
    from ._agent_help import agent_help
    from ._aliases import AliasGroup

    __all__ += ["agent_help", "app"]

    app = typer.Typer(
        help="Command line tools for the spotifyify Spotify client.",
        cls=AliasGroup,
        # Plain click help: no ANSI, no boxes, no pager.
        rich_markup_mode=None,
        # Completion installers are Typer's only interactive code path.
        add_completion=False,
        # Rich renders tracebacks as ANSI boxes; keep failures plain text.
        pretty_exceptions_enable=False,
        no_args_is_help=True,
        context_settings={"help_option_names": ["-h", "--help"], "color": False},
    )
    app.add_typer(tracks.app, name="tracks")
    app.add_typer(artists.app, name="artists")
    app.add_typer(albums.app, name="albums")
    app.add_typer(playlists.app, name="playlists")
    app.add_typer(shows.app, name="shows")
    app.add_typer(episodes.app, name="episodes")
    app.add_typer(library.app, name="library")
    app.add_typer(player.app, name="player")
    app.add_typer(users.app, name="users")
    quick.register(app)

    def _render_agent_help() -> str:
        return agent_help(typer.main.get_command(app))

    @app.command("agent-help", hidden=True)
    def agent_help_command() -> None:
        """Print the whole command tree and output contract in one shot."""
        typer.echo(_render_agent_help())

    @app.callback(invoke_without_command=True)
    def _root(
        agent: Annotated[
            bool,
            typer.Option(
                "--agent-help",
                help="Print the whole command tree and output contract in one shot.",
            ),
        ] = False,
    ) -> None:
        if agent:
            typer.echo(_render_agent_help())
            raise typer.Exit()


if __name__ == "__main__":
    main()
