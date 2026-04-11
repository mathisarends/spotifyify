import functools
import inspect
import logging
from typing import Callable

logger = logging.getLogger(__name__)


def deprecated[**P, T](reason: str = "") -> Callable[[Callable[P, T]], Callable[P, T]]:
    def decorator(func: Callable[P, T]) -> Callable[P, T]:
        @functools.wraps(func)
        async def async_wrapper(*args: P.args, **kwargs: P.kwargs) -> T:
            _log_deprecation_warning(func)
            return await func(*args, **kwargs)

        @functools.wraps(func)
        def sync_wrapper(*args: P.args, **kwargs: P.kwargs) -> T:
            _log_deprecation_warning(func)
            return func(*args, **kwargs)

        return async_wrapper if inspect.iscoroutinefunction(func) else sync_wrapper

    return decorator


def _log_deprecation_warning(func: Callable) -> None:
    logger.warning(f"{func.__qualname__} is deprecated")
