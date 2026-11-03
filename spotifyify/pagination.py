"""Pagination helpers shared by SDK iterators and the CLI."""

from collections.abc import AsyncIterator, Awaitable, Callable
from typing import Any
from urllib.parse import parse_qs, urlparse

from spotifyify.exceptions import SpotifyResponseError
from spotifyify.models import CursorPaging, Paging
from spotifyify.validation import page as validate_page


def next_offset(next_url: str, *, current: int, limit: int) -> int:
    query = parse_qs(urlparse(next_url).query)
    try:
        offset = int(query.get("offset", [current + limit])[0])
    except (ValueError, TypeError) as exc:
        raise SpotifyResponseError("Invalid pagination offset") from exc
    if offset <= current:
        raise SpotifyResponseError("Pagination did not advance")
    return offset


async def iter_offset_items[T](
    fetch: Callable[..., Awaitable[Paging[T]]],
    *,
    limit: int = 50,
    offset: int = 0,
    **kwargs: Any,
) -> AsyncIterator[T]:
    validate_page(limit, offset)
    while True:
        response = await fetch(limit=limit, offset=offset, **kwargs)
        for item in response.items or []:
            yield item
        if not response.next:
            return
        offset = next_offset(response.next, current=offset, limit=response.limit)


async def iter_cursor_items[T](
    fetch: Callable[..., Awaitable[CursorPaging[T]]],
    *,
    limit: int = 50,
    numeric: bool = False,
    **kwargs: Any,
) -> AsyncIterator[T]:
    validate_page(limit)
    visited: set[str] = set()
    while True:
        response = await fetch(limit=limit, **kwargs)
        for item in response.items or []:
            yield item
        if not response.next:
            return
        if response.next in visited:
            raise SpotifyResponseError("Cursor pagination did not advance")
        visited.add(response.next)
        query = parse_qs(urlparse(response.next).query)
        cursors = {key: query[key][0] for key in ("after", "before") if key in query}
        if len(cursors) != 1:
            raise SpotifyResponseError("Expected one cursor in the next-page URL")
        kwargs = {
            key: value
            for key, value in kwargs.items()
            if key not in {"after", "before"}
        }
        try:
            kwargs.update(
                {
                    key: int(value) if numeric else value
                    for key, value in cursors.items()
                }
            )
        except ValueError as exc:
            raise SpotifyResponseError("Invalid numeric pagination cursor") from exc
