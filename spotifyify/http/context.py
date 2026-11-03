"""Request options belong to one client and are isolated between async tasks."""

from contextvars import ContextVar
from dataclasses import dataclass, field

from spotifyify.http.retry_event import OnRetryHook


@dataclass
class RequestContext:
    access_token: ContextVar[str | None] = field(
        default_factory=lambda: ContextVar("spotify_access_token", default=None)
    )
    on_retry: ContextVar[OnRetryHook | None] = field(
        default_factory=lambda: ContextVar("spotify_retry_hook", default=None)
    )


# Compatibility context for standalone low-level clients. Public clients always
# create their own context and never consult these module-level variables.
default_context = RequestContext()
