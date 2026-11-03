"""Smoke test for the artists namespace: search, get, albums."""

import asyncio

from spotifyify import SpotifyClient


async def main() -> None:
    async with SpotifyClient() as sp:
        results = await sp.artists.search("Radiohead", limit=3)
        print(f"Found {results.total} artists for 'Radiohead':\n")

        for artist in results.items or []:
            print(f"  {artist.name}")

        items = [item for item in results.items or [] if item is not None]
        if not items:
            print("No results")
            return
        first = items[0]
        if not first.id:
            return
        full_artist = await sp.artists.get(first.id)
        print(f"\nArtist details for '{full_artist.name}':")

        discography = await sp.artists.albums(first.id, limit=5, include_groups="album")
        print(f"\nAlbums ({discography.total} total):")
        for album in discography.items or []:
            print(f"  {album.name} ({album.release_date})")


if __name__ == "__main__":
    asyncio.run(main())
