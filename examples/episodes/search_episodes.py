"""Smoke test for the episodes namespace: search, get, get_many."""

import asyncio
import os

from spotifyify import SpotifyClient


async def main() -> None:
    async with SpotifyClient() as sp:
        results = await sp.episodes.search(
            "machine learning",
            limit=5,
            market=os.environ.get("SPOTIFYIFY_MARKET", "DE"),
        )
        print(f"Found {results.total} episodes for 'machine learning':\n")

        for ep in results.items or []:
            if ep is None:
                continue
            duration_min = (ep.duration_ms or 0) // 60_000
            print(f"  {ep.name} ({duration_min} min)")

        items = [item for item in results.items or [] if item is not None]
        if not items:
            print("No results")
            return
        first = items[0]
        if not first.id:
            return
        full_ep = await sp.episodes.get(
            first.id, market=os.environ.get("SPOTIFYIFY_MARKET", "DE")
        )
        print(f"\nEpisode details for '{full_ep.name}':")
        print(f"  Show: {full_ep.show.name if full_ep.show else 'N/A'}")
        print(f"  Release date: {full_ep.release_date}")
        print(f"  Description: {(full_ep.description or '')[:120]}...")

        ids = [ep.id for ep in items[:3]]
        batch = await sp.episodes.get_many(
            ids, market=os.environ.get("SPOTIFYIFY_MARKET", "DE")
        )
        print(f"\nBatch fetch returned {len(batch)} episodes")


if __name__ == "__main__":
    asyncio.run(main())
