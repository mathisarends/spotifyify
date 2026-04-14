"""Smoke test for the artists namespace: find, get, top_tracks, albums, related."""

import asyncio
from spotifyify import Spotifyify


async def main() -> None:
    async with Spotifyify() as sp:
        results = await sp.artists.find("Radiohead", limit=3)
        print(f"Found {results.total} artists for 'Radiohead':\n")

        for artist in results.items:
            genres = ", ".join(artist.genres or [])
            print(
                f"  {artist.name} — followers: {artist.followers.total if artist.followers else 0}, genres: {genres}"
            )

        first = results.items[0]
        full_artist = await sp.artists.get(first.id)
        print(f"\nArtist details for '{full_artist.name}':")
        print(f"  Popularity: {full_artist.popularity}")

        top = await sp.artists.top_tracks(first.id)
        print(f"\nTop tracks ({len(top)}):")
        for i, track in enumerate(top[:5], 1):
            print(f"  {i}. {track.name} (popularity: {track.popularity})")

        discography = await sp.artists.albums(first.id, limit=5, include_groups="album")
        print(f"\nAlbums ({discography.total} total):")
        for album in discography.items:
            print(f"  {album.name} ({album.release_date})")

        related = await sp.artists.related(first.id)
        print(f"\nRelated artists ({len(related)}):")
        for artist in related[:5]:
            print(f"  {artist.name}")


asyncio.run(main())
