from __future__ import annotations

from typing import Any

from typer.core import TyperGroup

try:
    # Typer vendors its own copy of click; its UsageError is a different class
    # from click.UsageError, so catching the latter would silently miss.
    from typer._click.exceptions import UsageError
except ImportError:  # pragma: no cover - falls back to plain click errors.
    from click import UsageError

# Names an agent is likely to reach for that are not the canonical spelling.
# Tolerating them costs nothing; failing on them costs a --help round trip.
SYNONYMS: dict[str, str] = {
    "find": "search",
    "query": "search",
    "ls": "list",
    "show": "get",
    "get-many": "get",
    "getmany": "get",
    "song": "tracks",
    "songs": "tracks",
    "podcast": "shows",
    "podcasts": "shows",
    "playback": "player",
    "status": "state",
    "now-playing": "state",
    "current": "state",
    "next": "skip",
    "forward": "skip",
    "prev": "previous",
    "back": "previous",
    "enqueue": "add-to-queue",
    "queue-add": "add-to-queue",
    "resume": "play",
    "start": "play",
    "stop": "pause",
    "profile": "me",
    "whoami": "me",
    "saved-track": "saved-tracks",
    "saved-album": "saved-albums",
    "recent": "recently-played",
    "history": "recently-played",
}


def _candidates(name: str) -> list[str]:
    """Spellings to try, in order, before giving up on a command name."""
    normalized = name.strip().lower().replace("_", "-")
    tried = [normalized]
    if normalized in SYNONYMS:
        tried.append(SYNONYMS[normalized])
    # Plural/singular tolerance: `artist` and `artists` should both work.
    tried.append(f"{normalized}s")
    if normalized.endswith("s"):
        tried.append(normalized[:-1])
    return tried


class AliasGroup(TyperGroup):
    """A command group that accepts near-miss spellings instead of failing.

    Aliases resolve deterministically through an explicit table plus
    plural/singular normalization. Prefix matching is deliberately not
    supported: it would silently change meaning whenever a command is added.
    """

    def get_command(self, ctx: Any, name: str) -> Any:
        command = super().get_command(ctx, name)
        if command is not None:
            return command
        for candidate in _candidates(name):
            command = super().get_command(ctx, candidate)
            if command is not None:
                return command
        return None

    def resolve_command(self, ctx: Any, args: list[str]) -> Any:
        try:
            return super().resolve_command(ctx, args)
        except UsageError as exc:
            # Name the alternatives in the failure itself, so a wrong guess
            # costs one call rather than a --help round trip.
            message = getattr(exc, "message", None)
            if args and isinstance(message, str) and "No such command" in message:
                known = ", ".join(
                    name
                    for name in self.list_commands(ctx)
                    if not getattr(self.get_command(ctx, name), "hidden", False)
                )
                exc.message = f"{message} Available: {known}"
            raise
