"""Shared batching with bounded concurrency and predictable failure cleanup."""

import asyncio
from collections.abc import Awaitable, Callable, Sequence
from typing import cast

BATCH_TRACKS = 50
BATCH_ARTISTS = 50
BATCH_ALBUMS = 20
BATCH_SHOWS = 50
BATCH_EPISODES = 50
BATCH_FOLLOW = 50


async def gather_batches(action, ids: Sequence[str], size: int) -> list:
    """Compatibility helper backed by the bounded SDK worker pool."""
    results = await bounded_map(action, chunks(ids, size))
    return [item for result in results for item in result]


async def sequential_batches(action, ids: Sequence[str], size: int) -> None:
    for batch in chunks(ids, size):
        await action(batch)


def chunks[T](values: Sequence[T], size: int) -> list[list[T]]:
    if size < 1:
        raise ValueError("Batch size must be positive")
    return [list(values[index : index + size]) for index in range(0, len(values), size)]


async def bounded_map[T, R](
    action: Callable[[T], Awaitable[R]], values: Sequence[T], *, concurrency: int = 8
) -> list[R]:
    if concurrency < 1:
        raise ValueError("concurrency must be positive")
    indexed = iter(enumerate(values))
    results: list[R | None] = [None] * len(values)

    async def worker() -> None:
        for index, value in indexed:
            results[index] = await action(value)

    tasks = [
        asyncio.create_task(worker()) for _ in range(min(concurrency, len(values)))
    ]
    try:
        await asyncio.gather(*tasks)
    except BaseException:
        for task in tasks:
            task.cancel()
        await asyncio.gather(*tasks, return_exceptions=True)
        raise
    return cast(list[R], results)
