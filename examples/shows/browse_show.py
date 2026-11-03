"""Smoke test for the shows namespace: search, get, episodes."""

import asyncio
import os

from spotifyify import SpotifyClient


async def main() -> None:
    async with SpotifyClient() as sp:
        results = await sp.shows.search(
            "Lex Fridman", limit=3, market=os.environ.get("SPOTIFYIFY_MARKET", "DE")
        )
        print(f"Found {results.total} shows for 'Lex Fridman':\n")

        for show in results.items or []:
            print(f"  {show.name}")

        items = [item for item in results.items or [] if item is not None]
        if not items:
            print("No results")
            return
        first = items[0]
        if not first.id:
            return
        full_show = await sp.shows.get(
            first.id, market=os.environ.get("SPOTIFYIFY_MARKET", "DE")
        )
        print(f"\nShow details for '{full_show.name}':")
        print(f"  Total episodes: {full_show.total_episodes}")
        print(f"  Languages: {', '.join(full_show.languages or [])}")

        eps = await sp.shows.episodes(
            first.id, limit=5, market=os.environ.get("SPOTIFYIFY_MARKET", "DE")
        )
        print(f"\nLatest episodes ({eps.total} total):")
        for ep in eps.items or []:
            if ep is None:
                continue
            duration_min = (ep.duration_ms or 0) // 60_000
            print(f"  {ep.name} ({duration_min} min)")


if __name__ == "__main__":
    asyncio.run(main())
