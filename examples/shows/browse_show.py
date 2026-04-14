"""Smoke test for the shows namespace: find, get, episodes."""

import asyncio
from spotifyify import Spotifyify


async def main() -> None:
    async with Spotifyify() as sp:
        results = await sp.shows.find("Lex Fridman", limit=3)
        print(f"Found {results.total} shows for 'Lex Fridman':\n")

        for show in results.items:
            print(f"  {show.name} — {show.publisher}")

        first = results.items[0]
        full_show = await sp.shows.get(first.id)
        print(f"\nShow details for '{full_show.name}':")
        print(f"  Publisher: {full_show.publisher}")
        print(f"  Total episodes: {full_show.total_episodes}")
        print(f"  Languages: {', '.join(full_show.languages or [])}")

        eps = await sp.shows.episodes(first.id, limit=5)
        print(f"\nLatest episodes ({eps.total} total):")
        for ep in eps.items:
            duration_min = (ep.duration_ms or 0) // 60_000
            print(f"  {ep.name} ({duration_min} min)")


asyncio.run(main())
