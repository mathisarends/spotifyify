"""Smoke test for the episodes namespace: find, get, get_many."""

import asyncio
from spotifyify import Spotifyify


async def main() -> None:
    async with Spotifyify() as sp:
        results = await sp.episodes.find("machine learning", limit=5)
        print(f"Found {results.total} episodes for 'machine learning':\n")

        for ep in results.items:
            duration_min = (ep.duration_ms or 0) // 60_000
            print(f"  {ep.name} ({duration_min} min)")

        first = results.items[0]
        full_ep = await sp.episodes.get(first.id)
        print(f"\nEpisode details for '{full_ep.name}':")
        print(f"  Show: {full_ep.show.name if full_ep.show else 'N/A'}")
        print(f"  Release date: {full_ep.release_date}")
        print(f"  Description: {(full_ep.description or '')[:120]}...")

        ids = [ep.id for ep in results.items[:3]]
        batch = await sp.episodes.get_many(ids)
        print(f"\nBatch fetch returned {len(batch)} episodes")


asyncio.run(main())
