from contextvars import ContextVar

from spotifyify.http.retry_event import OnRetryHook

current_retry_hook: ContextVar[OnRetryHook | None] = ContextVar(
    "current_retry_hook",
    default=None,
)
