"""Smoke test for the tracks namespace: search, get, get_many."""

import asyncio

from spotifyify import SpotifyClient


async def main() -> None:
    async with SpotifyClient() as sp:
        results = await sp.tracks.search("Daft Punk Get Lucky", limit=3)
        print(f"Found {results.total} results for 'Daft Punk Get Lucky':\n")

        for track in results.items or []:
            artists = ", ".join(a.name or "Unknown" for a in (track.artists or []))
            print(f"  {track.name} — {artists} ({track.duration_ms}ms)")

        items = [item for item in results.items or [] if item is not None]
        if not items:
            print("No results")
            return
        first = items[0]
        if not first.id:
            return
        full_track = await sp.tracks.get(first.id)
        print(f"\nFull track details for '{full_track.name}':")
        print(f"  Album: {full_track.album.name if full_track.album else 'N/A'}")
        print(f"  Explicit: {full_track.explicit}")

        ids = [t.id for t in items if t.id]
        batch = await sp.tracks.get_many(ids)
        print(f"\nBatch fetch returned {len(batch)} tracks")
        for t in batch:
            print(f"  {t.name if t else 'Unavailable'}")


if __name__ == "__main__":
    asyncio.run(main())
