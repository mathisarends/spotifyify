import logging
from typing import Any

import httpx
from pydantic import BaseModel

from spotifyify.exceptions import SpotifyAPIError, SpotifyRateLimitError

JsonResponse = dict[str, Any] | list[Any] | None
logger = logging.getLogger(__name__)


def _parse_retry_after(value: str | None) -> float | None:
    if value is None:
        return None
    try:
        return max(0.0, float(value))
    except ValueError:
        return None


def parse_response(response: httpx.Response) -> JsonResponse:
    if response.status_code == 204:
        return None

    if response.status_code >= 400:
        try:
            data = response.json()
            error = data.get("error", data) if isinstance(data, dict) else data
            message = (
                error.get("message", response.text)
                if isinstance(error, dict)
                else str(error)
            )
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
                retry_after=_parse_retry_after(response.headers.get("Retry-After")),
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
    except ValueError:
        # Some playback endpoints answer 200 with an opaque, non-JSON body and
        # no content type. There is nothing structured to hand back, but it is
        # a success and must not surface as a decoding error.
        logger.debug(
            "Ignoring non-JSON success body: status_code=%d content_type=%s",
            response.status_code,
            response.headers.get("Content-Type"),
        )
        return None


def validate_response_model(
    parsed: JsonResponse,
    response_model: type[BaseModel] | None,
) -> Any:
    if response_model is None or parsed is None:
        return parsed
    if isinstance(parsed, list):
        logger.warning(
            "Unable to validate Spotify API response: expected object, got list"
        )
        raise SpotifyAPIError(500, "Expected object response but got list")
    return response_model.model_validate(parsed)
