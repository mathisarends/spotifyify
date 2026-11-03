import asyncio

from spotifyify import SpotifyClient, SpotifyScope


async def main() -> None:
    async with SpotifyClient(scopes=[SpotifyScope.USER_MODIFY_PLAYBACK_STATE]) as sp:
        results = await sp.tracks.search("Daft Punk Get Lucky", limit=5)

        for track in results.items or []:
            artists = ", ".join(a.name or "Unknown" for a in (track.artists or []))
            print(f"{track.name} — {artists}")

        items = [item for item in results.items or [] if item is not None]
        if not items:
            print("No results")
            return
        first = items[0]
        if not first.id:
            return

        if not first.uri:
            return
        await sp.player.play(uris=[first.uri])
        print(f"\nPlaying: {first.name}")


if __name__ == "__main__":
    asyncio.run(main())
