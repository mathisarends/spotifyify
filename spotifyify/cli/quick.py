from __future__ import annotations

from typing import Annotated, Any

import typer

from .core import (
    PLAYBACK_COLUMNS,
    _default_device_id,
    _default_market,
    _playback_summary,
    _settled_playback,
    is_fresh_track,
    plays_uri,
    spotify_client,
)
from .options import (
    FieldsOption,
    WaitOption,
    async_command,
    print_result,
)
from .player import CONTROL_SCOPES, _play_with_device_fallback

EXIT_NO_MATCH = 4


def _quoted(value: str) -> str:
    """Wrap a filter value for Spotify's search grammar."""
    return '"{}"'.format(value.replace('"', " ").strip())


def _build_query(
    words: list[str] | None,
    *,
    track: str | None,
    artist: str | None,
    album: str | None,
) -> str:
    """Turn the flags into a Spotify field-filtered search query."""
    parts: list[str] = []
    if track:
        parts.append(f"track:{_quoted(track)}")
    if artist:
        parts.append(f"artist:{_quoted(artist)}")
    if album:
        parts.append(f"album:{_quoted(album)}")
    parts.extend(words or [])
    return " ".join(part for part in parts if part).strip()


def _first(paging: Any) -> Any:
    items = getattr(paging, "items", None) or []
    return items[0] if items else None


def register(app: typer.Typer) -> None:
    """Attach the top-level resolve-and-play command."""

    @app.command("play")
    @async_command
    async def play(
        words: Annotated[
            list[str] | None,
            typer.Argument(help="Free-text search terms, added to the query as-is."),
        ] = None,
        track: Annotated[
            str | None, typer.Option("--track", "-t", help="Track name to match.")
        ] = None,
        artist: Annotated[
            str | None, typer.Option("--artist", "-a", help="Artist name to match.")
        ] = None,
        album: Annotated[
            str | None, typer.Option("--album", help="Album name to match.")
        ] = None,
        wait: WaitOption = True,
        fields: FieldsOption = None,
    ) -> None:
        """Find something and play it in one call.

        Resolves the top search hit and starts it, so no separate search-then-play
        round trip is needed:

          spotifyify play --artist Ikkimel --track "WHO'S THAT"

        A track name (or free text) plays that track. Without one, --album plays
        the album and --artist alone plays the artist.
        """
        query = _build_query(words, track=track, artist=artist, album=album)
        if not query:
            raise typer.BadParameter(
                "Give search terms or at least one of --track, --artist, --album."
            )
        # A track name, or bare free text, means "play this one thing".
        # Otherwise the broadest given filter becomes the playback context.
        wants_track = bool(track or words)
        wants_album = bool(album) and not wants_track
        market = _default_market()

        async with spotify_client(CONTROL_SCOPES) as spotify:
            if wants_track:
                hit = _first(await spotify.tracks.find(query, limit=1, market=market))
                uris, context_uri = ([hit.uri] if hit else None), None
            elif wants_album:
                hit = _first(await spotify.albums.find(query, limit=1, market=market))
                uris, context_uri = None, (hit.uri if hit else None)
            else:
                hit = _first(await spotify.artists.find(query, limit=1))
                uris, context_uri = None, (hit.uri if hit else None)

            if hit is None or not (uris or context_uri):
                typer.echo(f"No match for {query}", err=True)
                raise typer.Exit(EXIT_NO_MATCH)

            await _play_with_device_fallback(
                spotify,
                device_id=_default_device_id(),
                uris=uris,
                context_uri=context_uri,
            )
            # Wait for the thing we resolved, so the reported state is not the
            # track that happened to be playing already.
            until = plays_uri(uris[0]) if uris else is_fresh_track
            state = await _settled_playback(spotify, until=until, wait=wait)

        print_result(
            state,
            columns=PLAYBACK_COLUMNS,
            fields=fields,
            project=_playback_summary,
        )
