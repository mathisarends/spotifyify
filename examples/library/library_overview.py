"""Smoke test for the library namespace: saved items, top items, check."""

import asyncio
from collections import Counter

from spotifyify import SpotifyClient, SpotifyScope


async def main() -> None:
    async with SpotifyClient(
        scopes=[
            SpotifyScope.USER_LIBRARY_READ,
            SpotifyScope.USER_TOP_READ,
        ]
    ) as sp:
        saved = await sp.library.saved_tracks(limit=5)
        print(f"Saved tracks ({saved.total} total):")
        for item in saved.items or []:
            t = item.track
            if t is None:
                continue
            artists = ", ".join(a.name or "Unknown" for a in (t.artists or []))
            print(f"  {t.name} — {artists} (saved {item.added_at})")

        saved_albums = await sp.library.saved_albums(limit=3)
        print(f"\nSaved albums ({saved_albums.total} total):")
        for item in saved_albums.items or []:
            a = item.album
            if a is None:
                continue
            print(f"  {a.name} — {a.total_tracks} tracks (saved {item.added_at})")

        selected = [
            (item.track.id, item.track.name)
            for item in (saved.items or [])[:3]
            if item.track is not None and item.track.id is not None
        ]
        if selected:
            checks = await sp.library.check_tracks(
                [track_id for track_id, _ in selected]
            )
            print(
                f"\nCheck saved status: {list(zip([name for _, name in selected], checks, strict=True))}"
            )

        top = await sp.library.top_tracks(time_range="short_term", limit=10)
        print("\nTop tracks (short term):")
        for i, track in enumerate(top.items or [], 1):
            artists = ", ".join(a.name or "Unknown" for a in (track.artists or []))
            print(f"  {i:2}. {track.name} — {artists}")

        top_artists = await sp.library.top_artists(time_range="long_term", limit=20)
        genre_counts: Counter[str] = Counter(
            genre
            for artist in (top_artists.items or [])
            for genre in (artist.genres or [])
        )
        print("\nTop genres (long term):")
        for genre, count in genre_counts.most_common(5):
            print(f"  {count:3}x  {genre}")


if __name__ == "__main__":
    asyncio.run(main())
