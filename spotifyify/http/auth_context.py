from contextvars import ContextVar

current_access_token: ContextVar[str | None] = ContextVar(
    "current_access_token",
    default=None,
)
