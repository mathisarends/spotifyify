"""Smoke test for the albums namespace: search, get, tracks."""

import asyncio

from spotifyify import SpotifyClient


async def main() -> None:
    async with SpotifyClient() as sp:
        results = await sp.albums.search("Random Access Memories", limit=3)
        print(f"Found {results.total} albums for 'Random Access Memories':\n")

        for album in results.items or []:
            artists = ", ".join(a.name or "Unknown" for a in (album.artists or []))
            print(f"  {album.name} — {artists} ({album.release_date})")

        items = [item for item in results.items or [] if item is not None]
        if not items:
            print("No results")
            return
        first = items[0]
        if not first.id:
            return
        full_album = await sp.albums.get(first.id)
        print(f"\nAlbum details for '{full_album.name}':")
        print(f"  Total tracks: {full_album.total_tracks}")

        tracklist = await sp.albums.tracks(first.id, limit=5)
        print(f"\nFirst {len(tracklist.items or [])} tracks:")
        for i, t in enumerate(tracklist.items or [], 1):
            print(f"  {i}. {t.name} ({(t.duration_ms or 0) // 1000}s)")


if __name__ == "__main__":
    asyncio.run(main())
