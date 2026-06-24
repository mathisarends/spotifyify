"""Exercise Spotify rate limits and print retry events from the client hook.

This example intentionally sends many concurrent requests to the real Spotify
API so you can observe how spotifyify reacts to 429 responses and Retry-After.

Run with valid Spotify credentials in your environment:

    uv run python examples/retries.py --total 600 --concurrency 80

Increase --total and --concurrency if Spotify does not rate-limit your app.
"""

import argparse
import asyncio
from dataclasses import dataclass
from datetime import datetime

from spotifyify import RetryEvent, SpotifyAPIError, SpotifyRateLimitError, Spotifyify


DEFAULT_TRACK_ID = "4uLU6hMCjMI75M1A2tKUQC"


@dataclass(slots=True)
class RunStats:
    completed: int = 0
    failed: int = 0
    final_rate_limits: int = 0
    retry_events: int = 0


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Send many real Spotify API requests and print retry events.",
    )
    parser.add_argument(
        "--track-id",
        default=DEFAULT_TRACK_ID,
        help="Spotify track ID to fetch repeatedly.",
    )
    parser.add_argument(
        "--total",
        type=int,
        default=400,
        help="Total number of API requests to schedule.",
    )
    parser.add_argument(
        "--concurrency",
        type=int,
        default=60,
        help="Maximum number of requests in flight at once.",
    )
    parser.add_argument(
        "--max-retries",
        type=int,
        default=3,
        help="Retry budget per request.",
    )
    parser.add_argument(
        "--retry-backoff-seconds",
        type=float,
        default=0.25,
        help="Fallback exponential backoff when Retry-After is absent.",
    )
    return parser.parse_args()


async def main() -> None:
    args = parse_args()
    stats = RunStats()
    stats_lock = asyncio.Lock()
    semaphore = asyncio.Semaphore(args.concurrency)

    async def on_retry(event: RetryEvent) -> None:
        async with stats_lock:
            stats.retry_events += 1
            retry_events = stats.retry_events

        retry_after = event.response.headers.get("Retry-After", "<missing>")
        print(
            "[retry #{count}] status={status} retry={retry}/{max_retries} "
            "sleep={sleep:.2f}s retry_after={retry_after} retry_at={retry_at} "
            "path={path}".format(
                count=retry_events,
                status=event.status_code,
                retry=event.retry_number,
                max_retries=event.max_retries,
                sleep=event.retry_after,
                retry_after=retry_after,
                retry_at=event.retry_at.isoformat(),
                path=event.path,
            ),
            flush=True,
        )

    async def fetch_once(sp: Spotifyify, index: int) -> None:
        async with semaphore:
            try:
                await sp.tracks.get(args.track_id)
            except SpotifyRateLimitError as exc:
                async with stats_lock:
                    stats.failed += 1
                    stats.final_rate_limits += 1
                print(
                    "[final 429] retry_after={retry_after} retry_at={retry_at} "
                    "message={message}".format(
                        retry_after=exc.retry_after,
                        retry_at=exc.retry_at.isoformat() if exc.retry_at else None,
                        message=exc.message,
                    ),
                    flush=True,
                )
            except SpotifyAPIError:
                async with stats_lock:
                    stats.failed += 1
            else:
                async with stats_lock:
                    stats.completed += 1

            if index % 25 == 0 or index == args.total:
                async with stats_lock:
                    print(
                        "[progress] scheduled={index}/{total} ok={ok} "
                        "failed={failed} final_429={rate_limits} retries={retries}".format(
                            index=index,
                            total=args.total,
                            ok=stats.completed,
                            failed=stats.failed,
                            rate_limits=stats.final_rate_limits,
                            retries=stats.retry_events,
                        ),
                        flush=True,
                    )

    print(
        "Starting retry demo at {started}: total={total} concurrency={concurrency} "
        "max_retries={max_retries} track_id={track_id}".format(
            started=datetime.now().isoformat(timespec="seconds"),
            total=args.total,
            concurrency=args.concurrency,
            max_retries=args.max_retries,
            track_id=args.track_id,
        ),
        flush=True,
    )

    async with Spotifyify(
        max_retries=args.max_retries,
        retry_backoff_seconds=args.retry_backoff_seconds,
    ) as sp:
        async with sp.session(on_retry=on_retry):
            await asyncio.gather(
                *(fetch_once(sp, index) for index in range(1, args.total + 1)),
            )

    print(
        "Done: ok={ok} failed={failed} final_429={rate_limits} retry_events={retries}".format(
            ok=stats.completed,
            failed=stats.failed,
            rate_limits=stats.final_rate_limits,
            retries=stats.retry_events,
        ),
    )


if __name__ == "__main__":
    asyncio.run(main())
