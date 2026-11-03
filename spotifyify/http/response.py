import logging
from typing import Any

import httpx2
from pydantic import BaseModel, ValidationError

from spotifyify.exceptions import (
    SpotifyAPIError,
    SpotifyRateLimitError,
    SpotifyResponseError,
)
from spotifyify.http.retry_policy import parse_retry_after

JsonResponse = dict[str, Any] | list[Any] | None
logger = logging.getLogger(__name__)


def parse_response(
    response: httpx2.Response, *, allow_non_json: bool = False
) -> JsonResponse:
    if response.status_code == 204:
        return None

    if not 200 <= response.status_code < 300:
        try:
            data = response.json()
            error = data.get("error", data) if isinstance(data, dict) else data
            message = (
                error.get("message", response.text)
                if isinstance(error, dict)
                else str(error)
            )
            if isinstance(data, dict) and isinstance(error, str):
                message = data.get("error_description", message)
        except ValueError:
            data = None
            message = response.text
        logger.warning(
            "Spotify API returned an error response: status_code=%d message=%s",
            response.status_code,
            message,
        )
        if response.status_code == 429:
            raise SpotifyRateLimitError(
                message,
                data if isinstance(data, dict) else None,
                retry_after=parse_retry_after(response.headers.get("Retry-After")),
            )
        raise SpotifyAPIError(
            response.status_code,
            message,
            data if isinstance(data, dict) else None,
        )

    if not response.content:
        return None

    try:
        return response.json()
    except ValueError as exc:
        if allow_non_json:
            return None
        raise SpotifyResponseError(
            f"Expected JSON response, received HTTP {response.status_code}"
        ) from exc


def validate_model[T: BaseModel](model: type[T], data: Any) -> T:
    try:
        return model.model_validate(data)
    except ValidationError as exc:
        fields = ", ".join(
            ".".join(map(str, error["loc"]))
            for error in exc.errors(include_input=False)[:5]
        )
        raise SpotifyResponseError(
            f"Invalid {model.__name__} response ({fields or 'unexpected shape'})"
        ) from exc


def object_response(data: Any) -> dict[str, Any]:
    if not isinstance(data, dict):
        raise SpotifyResponseError("Expected an object response")
    return data


def list_response(data: Any, key: str | None = None) -> list[Any]:
    if key is not None:
        data = object_response(data).get(key)
    if not isinstance(data, list):
        raise SpotifyResponseError(
            f"Expected a list response{f' in {key}' if key else ''}"
        )
    return data


def validate_response_model(
    parsed: JsonResponse,
    response_model: type[BaseModel] | None,
) -> Any:
    if response_model is None:
        return parsed
    return validate_model(response_model, parsed)
