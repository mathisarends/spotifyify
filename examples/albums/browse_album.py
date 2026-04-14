"""Smoke test for the albums namespace: find, get, tracks, new_releases."""

import asyncio
from spotifyify import Spotifyify


async def main() -> None:
    async with Spotifyify() as sp:
        results = await sp.albums.find("Random Access Memories", limit=3)
        print(f"Found {results.total} albums for 'Random Access Memories':\n")

        for album in results.items:
            artists = ", ".join(a.name for a in (album.artists or []))
            print(f"  {album.name} — {artists} ({album.release_date})")

        first = results.items[0]
        full_album = await sp.albums.get(first.id)
        print(f"\nAlbum details for '{full_album.name}':")
        print(f"  Label: {full_album.label}")
        print(f"  Total tracks: {full_album.total_tracks}")
        print(f"  Popularity: {full_album.popularity}")

        tracklist = await sp.albums.tracks(first.id, limit=5)
        print(f"\nFirst {len(tracklist.items)} tracks:")
        for i, t in enumerate(tracklist.items, 1):
            print(f"  {i}. {t.name} ({t.duration_ms // 1000}s)")

        new = await sp.albums.new_releases(limit=5)
        print(f"\nNew releases ({new.total} total):")
        for album in new.items:
            artists = ", ".join(a.name for a in (album.artists or []))
            print(f"  {album.name} — {artists}")


asyncio.run(main())
