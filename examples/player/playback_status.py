"""Smoke test for the player namespace: state, devices, queue, recently_played."""

import asyncio
from spotifyify import Spotifyify, SpotifyScope


async def main() -> None:
    async with Spotifyify(
        scopes=[
            SpotifyScope.USER_READ_PLAYBACK_STATE,
            SpotifyScope.USER_READ_RECENTLY_PLAYED,
        ]
    ) as sp:
        devices = await sp.player.devices()
        print(f"Available devices ({len(devices)}):")
        for d in devices:
            active = " (active)" if d.is_active else ""
            print(f"  {d.name} — {d.type}{active}, volume: {d.volume_percent}%")

        state = await sp.player.state()
        if state and state.item:
            item = state.item
            print(f"\nNow playing: {item.name}")
            print(
                f"  Progress: {(state.progress_ms or 0) // 1000}s / {(item.duration_ms or 0) // 1000}s"
            )
            print(f"  Shuffle: {state.shuffle_state}, Repeat: {state.repeat_state}")
        else:
            print("\nNo active playback")

        queue = await sp.player.queue()
        if queue.queue:
            print(f"\nQueue ({len(queue.queue)} tracks):")
            for t in queue.queue[:5]:
                print(f"  {t.name}")
        else:
            print("\nQueue is empty")

        history = await sp.player.recently_played(limit=5)
        print("\nRecently played:")
        for item in history.items:
            track = item.track
            print(f"  {track.name} — played at {item.played_at}")


asyncio.run(main())
