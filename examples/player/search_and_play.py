import asyncio
from spotifyify import Spotifyify, SpotifyScope


async def main() -> None:
    async with Spotifyify(scopes=[SpotifyScope.USER_MODIFY_PLAYBACK_STATE]) as sp:
        results = await sp.tracks.find("Daft Punk Get Lucky", limit=5)

        for track in results.items:
            artists = ", ".join(a.name for a in (track.artists or []))
            print(f"{track.name} — {artists}")

        first = results.items[0]

        await sp.player.play(uris=[first.uri])
        print(f"\nPlaying: {first.name}")


asyncio.run(main())
