"""Smoke test for the playlists namespace: search, list, get, cover_image."""

import asyncio

from spotifyify import SpotifyClient, SpotifyScope


async def main() -> None:
    async with SpotifyClient(scopes=[SpotifyScope.PLAYLIST_READ_PRIVATE]) as sp:
        search = await sp.playlists.search("chill vibes", limit=3)
        print(f"Search results for 'chill vibes' ({search.total} total):")
        for pl in search.items or []:
            if pl is None:
                continue
            owner = pl.owner.display_name if pl.owner else "unknown"
            print(
                f"  {pl.name} — by {owner} ({pl.items.total if pl.items else 0} tracks)"
            )

        my_playlists = await sp.playlists.list(limit=5)
        print(f"\nMy playlists ({my_playlists.total} total):")
        for pl in my_playlists.items or []:
            if pl is None:
                continue
            print(
                f"  {pl.name} — {pl.items.total if pl.items else 0} items, public: {pl.public}"
            )

        if my_playlists.items:
            first = my_playlists.items[0]
            if first is None or not first.id:
                return
            full = await sp.playlists.get(first.id)
            print(f"\nPlaylist details for '{full.name}':")
            print(f"  Description: {full.description or 'N/A'}")

            images = await sp.playlists.cover_image(first.id)
            print(f"  Cover images: {len(images)}")
            for img in images:
                print(f"    {img.width}x{img.height} — {img.url[:60]}...")


if __name__ == "__main__":
    asyncio.run(main())
