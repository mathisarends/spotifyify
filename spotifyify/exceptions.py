from datetime import UTC, datetime, timedelta


class SpotifyError(Exception):
    """Base exception for all spotifyify errors."""


class SpotifyAPIError(SpotifyError):
    def __init__(
        self, status_code: int, message: str, details: dict | None = None
    ) -> None:
        self.status_code = status_code
        self.message = message
        self.details = details or {}
        super().__init__(f"{status_code}: {message}")


class SpotifyRateLimitError(SpotifyAPIError):
    def __init__(
        self,
        message: str,
        details: dict | None = None,
        *,
        retry_after: float | None = None,
    ) -> None:
        self.retry_after = retry_after
        self.retry_at = (
            datetime.now(UTC) + timedelta(seconds=retry_after)
            if retry_after is not None
            else None
        )
        super().__init__(429, message, details)


class SpotifyAuthError(SpotifyError):
    def __init__(self, message: str, *, code: str | None = None) -> None:
        self.code = code
        super().__init__(message)


class SpotifyTransportError(SpotifyError):
    """The request could not be completed at the HTTP transport layer."""


class SpotifyResponseError(SpotifyError):
    """A successful HTTP response did not match the expected API contract."""


class SpotifyUnsupportedOperation(SpotifyError):
    """An operation is unavailable in the selected Spotify API mode."""


class SpotifyBatchError(SpotifyError):
    """A multi-request mutation failed after some inputs were processed."""

    def __init__(
        self,
        operation: str,
        *,
        completed_items: int,
        total_items: int,
        snapshot_id: str | None,
    ) -> None:
        self.operation = operation
        self.completed_items = completed_items
        self.total_items = total_items
        self.snapshot_id = snapshot_id
        super().__init__(
            f"{operation} stopped after {completed_items}/{total_items} input items; the playlist may already be partially updated"
        )


SpotifyifyError = SpotifyError
