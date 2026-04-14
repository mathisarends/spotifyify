import asyncio
from spotifyify import Spotifyify, SpotifyScope


async def main() -> None:
    async with Spotifyify(scopes=[SpotifyScope.PLAYLIST_MODIFY_PRIVATE]) as sp:
        search = await sp.tracks.find("Boards of Canada Music Has the Right", limit=1)
        seed = search.items[0]

        recs = await sp.tracks.recommendations(
            seed_tracks=[seed.id], seed_genres=["ambient"], limit=10
        )
        uris = [t.uri for t in recs.tracks if t.uri]

        playlist = await sp.playlists.create("My Ambient Mix", public=False)
        await sp.playlists.add(playlist.id, uris)
        await sp.playlists.update(playlist.id, description=f"Seeded from '{seed.name}'")

        print(f"Created '{playlist.name}' with {len(uris)} tracks")


asyncio.run(main())
