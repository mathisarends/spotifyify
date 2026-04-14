"""Smoke test for the library namespace: saved items, top items, check."""

import asyncio
from collections import Counter
from spotifyify import Spotifyify, SpotifyScope


async def main() -> None:
    async with Spotifyify(
        scopes=[
            SpotifyScope.USER_LIBRARY_READ,
            SpotifyScope.USER_TOP_READ,
        ]
    ) as sp:
        saved = await sp.library.saved_tracks(limit=5)
        print(f"Saved tracks ({saved.total} total):")
        for item in saved.items:
            t = item.track
            artists = ", ".join(a.name for a in (t.artists or []))
            print(f"  {t.name} — {artists} (saved {item.added_at})")

        saved_albums = await sp.library.saved_albums(limit=3)
        print(f"\nSaved albums ({saved_albums.total} total):")
        for item in saved_albums.items:
            a = item.album
            print(f"  {a.name} — {a.total_tracks} tracks (saved {item.added_at})")

        if saved.items:
            ids = [item.track.id for item in saved.items[:3]]
            checks = await sp.library.check_tracks(ids)
            print(
                f"\nCheck saved status: {list(zip([item.track.name for item in saved.items[:3]], checks))}"
            )

        top = await sp.library.top_tracks(time_range="short_term", limit=10)
        print("\nTop tracks (short term):")
        for i, track in enumerate(top.items, 1):
            artists = ", ".join(a.name for a in (track.artists or []))
            print(f"  {i:2}. {track.name} — {artists}")

        top_artists = await sp.library.top_artists(time_range="long_term", limit=20)
        genre_counts: Counter[str] = Counter(
            genre for artist in top_artists.items for genre in (artist.genres or [])
        )
        print("\nTop genres (long term):")
        for genre, count in genre_counts.most_common(5):
            print(f"  {count:3}x  {genre}")


asyncio.run(main())
