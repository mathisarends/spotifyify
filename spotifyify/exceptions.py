from datetime import UTC, datetime, timedelta


class SpotifyifyError(Exception):
    """Base exception for all spotifyify errors."""


class SpotifyAPIError(SpotifyifyError):
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


class SpotifyAuthError(SpotifyifyError):
    pass
