import functools
import inspect
import sys
from collections.abc import Callable, Iterable
from typing import Any, TypeVar

F = TypeVar("F", bound=Callable[..., Any])


def coalesce_items(ids_or_uris: Iterable[str]) -> list[str]:
    return [str(v).strip() for v in ids_or_uris if str(v).strip()]


def coalesce_csv(ids_or_uris: Iterable[str]) -> str:
    return ",".join(coalesce_items(ids_or_uris))


def deprecated(reason: str) -> Callable[[F], F]:
    def decorator(func: F) -> F:
        if inspect.iscoroutinefunction(func):

            @functools.wraps(func)
            async def async_wrapper(*args: Any, **kwargs: Any) -> Any:
                print(f"warning: {reason}", file=sys.stderr)
                return await func(*args, **kwargs)

            return async_wrapper  # type: ignore[return-value]

        @functools.wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            print(f"warning: {reason}", file=sys.stderr)
            return func(*args, **kwargs)

        return wrapper  # type: ignore[return-value]

    return decorator
