from __future__ import annotations

SPOTIFY_API_BASE_URL = "https://api.spotify.com/v1"
SPOTIFY_OAUTH_TOKEN_URL = "https://accounts.spotify.com/api/token"


def normalize_scope(scope: str | list[str] | tuple[str, ...] | None) -> str | None:
    if scope is None:
        return None
    if isinstance(scope, str):
        chunks = [part.strip() for part in scope.replace(",", " ").split()]
        return " ".join(sorted(set(filter(None, chunks)))) or None
    if isinstance(scope, (list, tuple)):
        chunks = [str(part).strip() for part in scope]
        return " ".join(sorted(set(filter(None, chunks)))) or None
    raise TypeError("scope must be str, list[str], tuple[str, ...], or None")
