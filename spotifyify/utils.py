import functools
import inspect
import sys
from collections.abc import Callable, Iterable
from typing import Any, TypeVar

F = TypeVar("F", bound=Callable[..., Any])


def normalize_scopes(scopes: Iterable[str] | str | None) -> list[str]:
    if scopes is None:
        return []
    if isinstance(scopes, str):
        scopes = [scopes]
    parts: set[str] = set()
    for scope in scopes:
        if not isinstance(scope, str):
            raise TypeError("Scopes must be strings")
        parts.update(scope.replace(",", " ").split())
    return sorted(parts)


def coalesce_items(ids_or_uris: Iterable[str]) -> list[str]:
    if isinstance(ids_or_uris, (str, bytes)):
        raise ValueError(
            "Pass a collection of IDs or URIs, for example [item_id], rather than a single string"
        )
    result = []
    for value in ids_or_uris:
        if not isinstance(value, str):
            raise ValueError("IDs and URIs must be strings")
        if value.strip():
            result.append(value.strip())
    return result


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
