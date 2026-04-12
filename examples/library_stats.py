import asyncio
from collections import Counter
from spotifyify import Spotifyify, SpotifyScope


async def main() -> None:
    async with Spotifyify(
        scopes=[SpotifyScope.USER_TOP_READ, SpotifyScope.USER_LIBRARY_READ]
    ) as sp:
        top_tracks = await sp.library.top_tracks(time_range="medium_term", limit=10)
        print("Top tracks:")
        for i, track in enumerate(top_tracks.items, 1):
            artists = ", ".join(a.name for a in (track.artists or []))
            print(f"  {i:2}. {track.name} — {artists}")

        top_artists = await sp.library.top_artists(time_range="long_term", limit=50)
        genre_counts: Counter[str] = Counter(
            genre for artist in top_artists.items for genre in (artist.genres or [])
        )
        print("\nTop genres:")
        for genre, count in genre_counts.most_common(8):
            print(f"  {count:3}x  {genre}")


asyncio.run(main())
