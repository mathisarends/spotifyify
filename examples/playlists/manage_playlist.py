import asyncio

from spotifyify import SpotifyClient, SpotifyScope


async def main() -> None:
    async with SpotifyClient(scopes=[SpotifyScope.PLAYLIST_MODIFY_PRIVATE]) as sp:
        search = await sp.tracks.search("Boards of Canada", limit=5)
        uris = [t.uri for t in (search.items or []) if t.uri]

        playlist = await sp.playlists.create("My Boards of Canada Mix", public=False)
        if not playlist.id:
            return
        await sp.playlists.add(playlist.id, uris)
        await sp.playlists.update(playlist.id, description="Boards of Canada tracks")

        print(f"Created '{playlist.name}' with {len(uris)} tracks")


if __name__ == "__main__":
    asyncio.run(main())
