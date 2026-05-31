"""Load the first page of items from a public Spotify playlist."""

import asyncio

from spotifyify import Spotifyify
from spotifyify.cache_handler import MemoryCacheHandler

PLAYLIST_ID = "2hmLDliFT9mW84XHxRUzwx"


async def main() -> None:
    async with Spotifyify(cache_handler=MemoryCacheHandler()) as sp:
        page = await sp.playlists.tracks(PLAYLIST_ID, limit=10)
        print(f"Public playlist: {PLAYLIST_ID}")
        print(f"Items: {page.total}")

        for playlist_item in page.items or []:
            item = playlist_item.item or playlist_item.track
            if item is None:
                continue
            print(f"  {item.type}: {item.name}")


if __name__ == "__main__":
    asyncio.run(main())
