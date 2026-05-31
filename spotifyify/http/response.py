import logging
from typing import Any

import httpx
from pydantic import BaseModel

from spotifyify.exceptions import SpotifyAPIError

JsonResponse = dict[str, Any] | list[Any] | None
logger = logging.getLogger(__name__)


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
        raise SpotifyAPIError(
            response.status_code,
            message,
            data if isinstance(data, dict) else None,
        )

    if not response.content:
        return None

    return response.json()


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
