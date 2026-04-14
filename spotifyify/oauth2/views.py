from enum import StrEnum
from pydantic import BaseModel


class TokenFormPayload(BaseModel):
    grant_type: str
    refresh_token: str | None = None


class SpotifyScope(StrEnum):
    USER_READ_PLAYBACK_STATE = "user-read-playback-state"
    USER_MODIFY_PLAYBACK_STATE = "user-modify-playback-state"
    USER_LIBRARY_READ = "user-library-read"
    USER_LIBRARY_MODIFY = "user-library-modify"
    USER_TOP_READ = "user-top-read"
    USER_READ_RECENTLY_PLAYED = "user-read-recently-played"
    PLAYLIST_MODIFY_PUBLIC = "playlist-modify-public"
    PLAYLIST_MODIFY_PRIVATE = "playlist-modify-private"
    PLAYLIST_READ_PRIVATE = "playlist-read-private"
