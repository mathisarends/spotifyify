from __future__ import annotations

try:
    import typer
except ImportError:  # pragma: no cover - exercised by installed package users.
    typer = None

from ._core import (
    INSTALL_MESSAGE,
    _filter_fields,
    _get_path,
    _parse_scopes,
    _split_values,
    _table,
)

__all__ = [
    "INSTALL_MESSAGE",
    "main",
    "typer",
    "_filter_fields",
    "_get_path",
    "_parse_scopes",
    "_split_values",
    "_table",
]


def main() -> None:
    if typer is None:
        raise SystemExit(INSTALL_MESSAGE)
    app()


if typer is not None:
    from . import (
        albums,
        artists,
        episodes,
        library,
        player,
        playlists,
        shows,
        tracks,
        users,
    )

    app = typer.Typer(help="Command line tools for the spotifyify Spotify client.")
    app.add_typer(tracks.app, name="tracks")
    app.add_typer(artists.app, name="artists")
    app.add_typer(albums.app, name="albums")
    app.add_typer(playlists.app, name="playlists")
    app.add_typer(shows.app, name="shows")
    app.add_typer(episodes.app, name="episodes")
    app.add_typer(library.app, name="library")
    app.add_typer(player.app, name="player")
    app.add_typer(users.app, name="users")


if __name__ == "__main__":
    main()
