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


class SpotifyAuthError(SpotifyifyError):
    pass
