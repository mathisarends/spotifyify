import asyncio
from spotifyify import Spotifyify, SpotifyScope


async def main() -> None:
    async with Spotifyify(scopes=[SpotifyScope.PLAYLIST_MODIFY_PRIVATE]) as sp:
        search = await sp.tracks.find("Boards of Canada", limit=5)
        uris = [t.uri for t in search.items if t.uri]

        playlist = await sp.playlists.create("My Boards of Canada Mix", public=False)
        await sp.playlists.add(playlist.id, uris)
        await sp.playlists.update(playlist.id, description="Boards of Canada tracks")

        print(f"Created '{playlist.name}' with {len(uris)} tracks")


asyncio.run(main())
