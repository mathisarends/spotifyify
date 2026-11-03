"""Read a playlist the authenticated user owns or collaborates on."""

import argparse
import asyncio

from spotifyify import SpotifyClient


async def main(playlist_id: str) -> None:
    async with SpotifyClient() as spotify:
        async for playlist_item in spotify.playlists.iter_items(playlist_id):
            item = playlist_item.item
            if item is not None:
                print(f"{item.type}: {item.name}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("playlist_id", help="A playlist you own or collaborate on")
    asyncio.run(main(parser.parse_args().playlist_id))
