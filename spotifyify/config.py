from enum import StrEnum


class ApiMode(StrEnum):
    """Spotify's supported endpoint contracts, not an automatic quota upgrade."""

    DEVELOPMENT = "development"
    EXTENDED = "extended"
