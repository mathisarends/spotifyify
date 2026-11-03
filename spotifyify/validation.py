"""Validate user inputs before any authentication or HTTP side effects."""

from typing import Any


def integer(
    name: str, value: int, *, minimum: int = 0, maximum: int | None = None
) -> None:
    if (
        type(value) is not int
        or value < minimum
        or (maximum is not None and value > maximum)
    ):
        bound = f"{minimum}..{maximum}" if maximum is not None else f">= {minimum}"
        raise ValueError(f"{name} must be an integer {bound}")


def page(limit: int, offset: int = 0) -> None:
    integer("limit", limit, minimum=1, maximum=50)
    integer("offset", offset)


def market(value: str | None) -> str | None:
    if value is None:
        return None
    if len(value) != 2 or not value.isascii() or not value.isalpha():
        raise ValueError("market/country must be a two-letter country code")
    return value.upper()


def spotify_id(value: str) -> str:
    if (
        not isinstance(value, str)
        or not value.strip()
        or any(
            character.isspace() or character in "/?#:" for character in value.strip()
        )
    ):
        raise ValueError(
            "Expected a nonempty Spotify ID, without a URI, URL, or path separators"
        )
    return value.strip()


def uri(value: str, *, kinds: tuple[str, ...] = ("track", "episode")) -> str:
    if not isinstance(value, str):
        raise ValueError("Expected a Spotify URI")
    parts = value.split(":")
    if len(parts) != 3 or parts[0] != "spotify" or parts[1] not in kinds:
        raise ValueError(f"Expected a Spotify URI for {', '.join(kinds)}")
    spotify_id(parts[2])
    return value


def playback_offset(value: dict[str, Any]) -> None:
    if set(value) == {"position"}:
        integer("offset.position", value["position"])
    elif set(value) == {"uri"}:
        uri(value["uri"])
    else:
        raise ValueError("offset must contain exactly one of position or uri")
