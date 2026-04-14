"""Smoke test for the playlists namespace: find, list, get, cover_image."""

import asyncio
from spotifyify import Spotifyify, SpotifyScope


async def main() -> None:
    async with Spotifyify(scopes=[SpotifyScope.PLAYLIST_READ_PRIVATE]) as sp:
        search = await sp.playlists.find("chill vibes", limit=3)
        print(f"Search results for 'chill vibes' ({search.total} total):")
        for pl in search.items:
            if pl is None:
                continue
            owner = pl.owner.display_name if pl.owner else "unknown"
            print(
                f"  {pl.name} — by {owner} ({pl.tracks.total if pl.tracks else 0} tracks)"
            )

        my_playlists = await sp.playlists.list(limit=5)
        print(f"\nMy playlists ({my_playlists.total} total):")
        for pl in my_playlists.items or []:
            print(
                f"  {pl.name} — {pl.tracks.total if pl.tracks else 0} tracks, public: {pl.public}"
            )

        if my_playlists.items:
            first = my_playlists.items[0]
            full = await sp.playlists.get(first.id)
            print(f"\nPlaylist details for '{full.name}':")
            print(f"  Description: {full.description or 'N/A'}")

            images = await sp.playlists.cover_image(first.id)
            print(f"  Cover images: {len(images)}")
            for img in images:
                print(f"    {img.width}x{img.height} — {img.url[:60]}...")


asyncio.run(main())
