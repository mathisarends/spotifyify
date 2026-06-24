from __future__ import annotations

import json
from collections.abc import Awaitable, Callable, Mapping, Sequence
from typing import Any

from pydantic import BaseModel

from spotifyify import Spotifyify, SpotifyScope

try:
    import typer
except ImportError:  # pragma: no cover - exercised by installed package users.
    typer = None


Jsonable = BaseModel | list[Any] | dict[str, Any] | str | int | float | bool | None
AsyncCommand = Callable[[Spotifyify], Awaitable[Jsonable]]

DEFAULT_LIMIT = 10
INSTALL_MESSAGE = "Install the CLI dependencies with: uv add spotifyify[cli]"


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


def _parse_scopes(scope_values: Sequence[str]) -> list[SpotifyScope | str]:
    scopes: list[SpotifyScope | str] = []
    for value in _split_values(scope_values):
        try:
            scopes.append(SpotifyScope(value))
        except ValueError:
            scopes.append(value)
    return scopes


def _coalesce_scopes(scope_values: Sequence[str] | None) -> Sequence[str]:
    return scope_values or ()


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
    if isinstance(value, list):
        return ", ".join(_format_value(item) for item in value)
    if isinstance(value, dict):
        if "name" in value:
            return str(value["name"])
        if "id" in value:
            return str(value["id"])
        return json.dumps(value, ensure_ascii=False, separators=(",", ":"))
    return str(value)


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


def _table(headers: Sequence[str], rows: Sequence[Sequence[str]]) -> str:
    if not rows:
        return "No results."

    widths = [
        max(len(header), *(len(row[index]) for row in rows))
        for index, header in enumerate(headers)
    ]
    rendered = [
        "  ".join(header.ljust(widths[index]) for index, header in enumerate(headers))
    ]
    rendered.append("  ".join("-" * width for width in widths))
    rendered.extend(
        "  ".join(value.ljust(widths[index]) for index, value in enumerate(row))
        for row in rows
    )
    return "\n".join(rendered)


def _print_json(value: Jsonable, *, fields: Sequence[str] = ()) -> None:
    payload = _filter_fields(_as_jsonable(value), fields)
    text = json.dumps(payload, indent=2, ensure_ascii=False)
    if typer is None:
        print(text)
        return
    typer.echo(text)


def _print_table(
    value: Jsonable,
    columns: Sequence[str],
    *,
    fields: Sequence[str] = (),
) -> None:
    selected_columns = fields or columns
    rows = [
        [_format_value(_get_path(item, column)) for column in selected_columns]
        for item in _items(value)
    ]
    headers = [column.replace(".", " ").title() for column in selected_columns]
    text = _table(headers, rows)
    if typer is None:
        print(text)
        return
    typer.echo(text)


def _print_success(value: str | None = None) -> None:
    if typer is None:
        print(value or "OK")
        return
    typer.echo(value or "OK")


async def _run(command: AsyncCommand, *, scopes: Sequence[str]) -> Jsonable:
    async with Spotifyify(scopes=_parse_scopes(scopes)) as spotify:
        return await command(spotify)
