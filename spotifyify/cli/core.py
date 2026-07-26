from __future__ import annotations

import asyncio
import json
import os
import re
from collections.abc import AsyncGenerator, Awaitable, Callable, Mapping, Sequence
from contextlib import asynccontextmanager
from typing import Any

from pydantic import BaseModel

from spotifyify import Spotifyify, SpotifyScope

try:
    import typer
except ImportError:  # pragma: no cover - exercised by installed package users.
    typer = None


Jsonable = BaseModel | list[Any] | dict[str, Any] | str | int | float | bool | None
DEFAULT_LIMIT = 10
INSTALL_MESSAGE = "Install the CLI dependencies with: uv add spotifyify[cli]"

RAW_ENV_VAR = "SPOTIFYIFY_RAW"
MARKET_ENV_VAR = "SPOTIFYIFY_MARKET"
DEVICE_ENV_VAR = "SPOTIFYIFY_DEVICE_ID"

_market_override: str | None = None
_device_override: str | None = None

# Table cells are single-line by construction, so anything that could forge a
# row boundary or smuggle escape sequences is folded into a single space.
_CONTROL_CHARACTERS = re.compile(r"[\x00-\x1f\x7f]")


def _as_jsonable(value: Jsonable) -> Any:
    if isinstance(value, BaseModel):
        return value.model_dump(mode="json", exclude_none=True)
    if isinstance(value, list):
        return [_as_jsonable(item) for item in value]
    if isinstance(value, dict):
        return {key: _as_jsonable(item) for key, item in value.items()}
    return value


def _split_values(values: Sequence[str] | None) -> list[str]:
    if not values:
        return []
    items: list[str] = []
    for raw_value in values:
        items.extend(value for value in raw_value.replace(",", " ").split() if value)
    return items


def _merge_scopes(*scope_groups: Sequence[SpotifyScope]) -> list[SpotifyScope]:
    merged: list[SpotifyScope] = []
    for group in scope_groups:
        merged.extend(scope for scope in group if scope not in merged)
    return merged


def _parse_json_object(
    raw_value: str | None, option_name: str
) -> dict[str, Any] | None:
    if not raw_value:
        return None
    try:
        value = json.loads(raw_value)
    except json.JSONDecodeError as exc:
        message = f"{option_name} must be a JSON object: {exc.msg}"
        if typer is None:
            raise ValueError(message) from exc
        raise typer.BadParameter(message) from exc
    if not isinstance(value, dict):
        message = f"{option_name} must be a JSON object"
        if typer is None:
            raise ValueError(message)
        raise typer.BadParameter(message)
    return value


def _get_path(value: Any, path: str) -> Any:
    current = value
    for part in path.split("."):
        if isinstance(current, Mapping):
            current = current.get(part)
        elif isinstance(current, Sequence) and not isinstance(current, str):
            try:
                current = current[int(part)]
            except (ValueError, IndexError):
                return None
        else:
            current = getattr(current, part, None)
        if current is None:
            return None
    return current


def _filter_fields(value: Any, fields: Sequence[str]) -> Any:
    if not fields:
        return value
    if isinstance(value, list):
        return [_filter_fields(item, fields) for item in value]
    return {field: _get_path(value, field) for field in fields}


def _format_value(value: Any) -> str:
    value = _as_jsonable(value)
    if value is None:
        return ""
    if isinstance(value, bool):
        return "true" if value else "false"
    if isinstance(value, list):
        return ", ".join(_format_value(item) for item in value)
    if isinstance(value, dict):
        if "name" in value:
            return str(value["name"])
        if "id" in value:
            return str(value["id"])
        return json.dumps(value, ensure_ascii=False, separators=(",", ":"))
    return str(value)


def _cell(value: Any) -> str:
    """Render one field as a single-line, escape-free table cell."""
    return _CONTROL_CHARACTERS.sub(" ", _format_value(value))


def _project(value: Any) -> Any:
    """Reduce a field to its useful part, keeping JSON types intact.

    Nested Spotify objects collapse to their name, so a column reads
    `"artists": ["Ikkimel"]` rather than two screens of artist objects, while
    numbers and booleans stay numbers and booleans.
    """
    value = _as_jsonable(value)
    if isinstance(value, list):
        return [_project(item) for item in value]
    if isinstance(value, dict):
        for key in ("name", "id"):
            if key in value:
                return value[key]
    return value


def _rows(value: Any, columns: Sequence[str]) -> list[dict[str, Any]]:
    """The command's declared columns, in order, for every item in the result."""
    return [
        {column: _project(_get_path(item, column)) for column in columns}
        for item in _items(value)
    ]


def _items(value: Any) -> list[Any]:
    value = _as_jsonable(value)
    if isinstance(value, dict) and isinstance(value.get("items"), list):
        return value["items"]
    if isinstance(value, dict) and isinstance(value.get("queue"), list):
        return value["queue"]
    if isinstance(value, list):
        return value
    if value is None:
        return []
    return [value]


def _sort_key(value: Any) -> tuple[int, float, str]:
    """Total order across mixed types so sorting never raises and never varies."""
    value = _as_jsonable(value)
    if value is None:
        return (2, 0.0, "")
    if isinstance(value, bool):
        return (0, float(value), "")
    if isinstance(value, (int, float)):
        return (0, float(value), "")
    return (1, 0.0, _cell(value).casefold())


def _sort_items(items: Sequence[Any], specs: Sequence[str]) -> list[Any]:
    """Stable multi-key sort; ties keep the order Spotify returned them in."""
    ordered = list(items)
    for spec in reversed(list(specs)):
        descending = spec.startswith("-")
        path = spec[1:] if descending else spec
        if not path:
            continue
        ordered.sort(
            key=lambda item: _sort_key(_get_path(item, path)), reverse=descending
        )
    return ordered


def _replace_collection(
    payload: Any, transform: Callable[[list[Any]], list[Any]]
) -> Any:
    """Apply a row transform to the item list, wherever the envelope keeps it."""
    if isinstance(payload, dict):
        for key in ("items", "queue"):
            if isinstance(payload.get(key), list):
                return {**payload, key: transform(payload[key])}
        return payload
    if isinstance(payload, list):
        return transform(payload)
    return payload


def _apply_sort(value: Any, specs: Sequence[str]) -> Any:
    if not specs:
        return value
    return _replace_collection(
        _as_jsonable(value), lambda items: _sort_items(items, specs)
    )


def _set_default_market(value: str | None) -> None:
    """Record the --market value from the root command, for this process only."""
    global _market_override
    _market_override = value


def _set_default_device_id(value: str | None) -> None:
    """Record the --device-id value from the root command, for this process only."""
    global _device_override
    _device_override = value


def _default_market() -> str | None:
    """Root --market flag, then the environment, then no market at all."""
    return _market_override or os.environ.get(MARKET_ENV_VAR) or None


def _default_device_id() -> str | None:
    """Root --device-id flag, then the environment, then no device at all."""
    return _device_override or os.environ.get(DEVICE_ENV_VAR) or None


def _is_raw_output() -> bool:
    return os.environ.get(RAW_ENV_VAR) == "1"


def _echo(text: str) -> None:
    if typer is None:
        print(text)
        return
    typer.echo(text)


def _print_json(value: Any) -> None:
    _echo(json.dumps(_as_jsonable(value), indent=2, ensure_ascii=False))


@asynccontextmanager
async def spotify_client(
    scopes: Sequence[SpotifyScope] = (),
) -> AsyncGenerator[Spotifyify, None]:
    """Open the async Spotify client used by one explicit CLI command."""
    async with Spotifyify(scopes=scopes) as spotify:
        yield spotify


# --------------------------------------------------------------------------- #
# Batching — one CLI call fans out to as many API calls as Spotify's id limits
# require, instead of making the caller loop.
# --------------------------------------------------------------------------- #

# Maximum ids Spotify accepts per request, per endpoint family.
BATCH_TRACKS = 50
BATCH_ARTISTS = 50
BATCH_ALBUMS = 20
BATCH_SHOWS = 50
BATCH_EPISODES = 50
BATCH_FOLLOW = 50


def _chunked(values: Sequence[str], size: int) -> list[list[str]]:
    if not values:
        return []
    return [list(values[index : index + size]) for index in range(0, len(values), size)]


async def _gather_batches(
    action: Callable[[list[str]], Awaitable[Sequence[Any]]],
    ids: Sequence[str],
    size: int,
) -> list[Any]:
    """Fan out reads concurrently, then concatenate in request order."""
    chunks = _chunked(ids, size)
    if not chunks:
        return []
    results = await asyncio.gather(*(action(chunk) for chunk in chunks))
    return [item for result in results for item in result]


async def _sequential_batches(
    action: Callable[[list[str]], Awaitable[Any]],
    ids: Sequence[str],
    size: int,
) -> None:
    """Apply writes chunk by chunk so partial failures stay comprehensible."""
    for chunk in _chunked(ids, size):
        await action(chunk)


# --------------------------------------------------------------------------- #
# Playback summaries — mutations answer with the state they produced.
# --------------------------------------------------------------------------- #

PLAYBACK_COLUMNS = ("state", "track", "artists", "device")
SETTLE_ATTEMPTS = 4
SETTLE_DELAY_SECONDS = 0.25

Predicate = Callable[[Any], bool]


def _playback_summary(state: Any) -> dict[str, Any]:
    """A flat, fixed-key view of playback that mutations and reads both emit."""
    if state is None:
        return {
            "state": "stopped",
            "track": "",
            "artists": [],
            "album": "",
            "device": "",
            "progress_ms": None,
            "duration_ms": None,
            "shuffle": None,
            "repeat": "",
            "uri": "",
        }
    payload = _as_jsonable(state)
    item = payload.get("item") or {}
    artists = item.get("artists") or []
    show = item.get("show") or {}
    album = item.get("album") or {}
    return {
        "state": "playing" if payload.get("is_playing") else "paused",
        "track": item.get("name") or "",
        # A list here too, matching how every other command reports artists.
        "artists": [artist.get("name") or "" for artist in artists]
        or ([show["publisher"]] if show.get("publisher") else []),
        "album": album.get("name") or show.get("name") or "",
        "device": (payload.get("device") or {}).get("name") or "",
        "progress_ms": payload.get("progress_ms"),
        "duration_ms": item.get("duration_ms"),
        "shuffle": payload.get("shuffle_state"),
        "repeat": payload.get("repeat_state") or "",
        "uri": item.get("uri") or "",
    }


def is_playing(state: Any) -> bool:
    return bool(getattr(state, "is_playing", False))


def is_paused(state: Any) -> bool:
    return state is not None and not getattr(state, "is_playing", False)


def is_fresh_track(state: Any) -> bool:
    """A just-started track: playing and barely into its runtime."""
    return is_playing(state) and (getattr(state, "progress_ms", None) or 0) < 5000


def plays_uri(uri: str | None) -> Predicate:
    """Wait for the track we actually asked for.

    `is_playing` alone is satisfied immediately by whatever was already playing,
    which would report the previous track as if it were the new one.
    """
    if uri is None:
        return is_fresh_track

    def matches(state: Any) -> bool:
        return (
            is_playing(state)
            and getattr(getattr(state, "item", None), "uri", None) == uri
        )

    return matches


async def _settled_playback(
    spotify: Spotifyify,
    *,
    until: Predicate | None = None,
    wait: bool = True,
) -> Any:
    """Read playback back after a mutation, briefly waiting for it to take effect.

    Spotify applies playback commands asynchronously, so an immediate read can
    still describe the previous track. Polling here costs a fraction of a second
    but saves the caller a whole second round trip.
    """
    attempts = SETTLE_ATTEMPTS if (wait and until is not None) else 1
    state = None
    for attempt in range(attempts):
        state = await spotify.player.state()
        if until is None or until(state):
            break
        if attempt < attempts - 1:
            await asyncio.sleep(SETTLE_DELAY_SECONDS)
    return state
