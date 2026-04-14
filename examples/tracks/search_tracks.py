"""Smoke test for the tracks namespace: find, get, get_many."""

import asyncio
from spotifyify import Spotifyify


async def main() -> None:
    async with Spotifyify() as sp:
        results = await sp.tracks.find("Daft Punk Get Lucky", limit=3)
        print(f"Found {results.total} results for 'Daft Punk Get Lucky':\n")

        for track in results.items:
            artists = ", ".join(a.name for a in (track.artists or []))
            print(f"  {track.name} — {artists} ({track.duration_ms}ms)")

        first = results.items[0]
        full_track = await sp.tracks.get(first.id)
        print(f"\nFull track details for '{full_track.name}':")
        print(f"  Album: {full_track.album.name if full_track.album else 'N/A'}")
        print(f"  Explicit: {full_track.explicit}")

        ids = [t.id for t in results.items]
        batch = await sp.tracks.get_many(ids)
        print(f"\nBatch fetch returned {len(batch)} tracks")
        for t in batch:
            print(f"  {t.name}")


asyncio.run(main())
