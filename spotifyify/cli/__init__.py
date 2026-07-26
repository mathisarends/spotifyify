import sys
from typing import Annotated

try:
    import typer
except ImportError:  # pragma: no cover - exercised by installed package users.
    typer = None

from .core import (
    INSTALL_MESSAGE,
    apply_sort,
    cell,
    filter_fields,
    get_path,
    playback_summary,
    rows,
    set_default_device_id,
    set_default_market,
    sort_items,
    split_values,
)

__all__ = [
    "INSTALL_MESSAGE",
    "main",
    "typer",
    "apply_sort",
    "cell",
    "filter_fields",
    "get_path",
    "playback_summary",
    "rows",
    "sort_items",
    "split_values",
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

    __all__ += ["app"]

    app = typer.Typer(
        help="Command line tools for the spotifyify Spotify client.",
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

    @app.callback(invoke_without_command=True)
    def _root(
        market: Annotated[
            str | None,
            typer.Option(
                "--market",
                "-m",
                help="Default ISO 3166-1 alpha-2 market code for every command "
                "in this invocation. Falls back to SPOTIFYIFY_MARKET.",
            ),
        ] = None,
        device_id: Annotated[
            str | None,
            typer.Option(
                "--device-id",
                help="Default Spotify Connect device for every playback command "
                "in this invocation. Falls back to SPOTIFYIFY_DEVICE_ID.",
            ),
        ] = None,
    ) -> None:
        set_default_market(market)
        set_default_device_id(device_id)


if __name__ == "__main__":
    main()
