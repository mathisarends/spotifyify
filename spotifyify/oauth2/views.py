from enum import StrEnum

from pydantic import BaseModel


class TokenFormPayload(BaseModel):
    grant_type: str
    refresh_token: str | None = None
    code: str | None = None
    redirect_uri: str | None = None


class SpotifyScope(StrEnum):
    USER_FOLLOW_READ = "user-follow-read"
    USER_FOLLOW_MODIFY = "user-follow-modify"
    USER_READ_PRIVATE = "user-read-private"
    USER_READ_EMAIL = "user-read-email"
    USER_READ_PLAYBACK_POSITION = "user-read-playback-position"
    PLAYLIST_READ_COLLABORATIVE = "playlist-read-collaborative"
    USER_READ_PLAYBACK_STATE = "user-read-playback-state"
    USER_MODIFY_PLAYBACK_STATE = "user-modify-playback-state"
    USER_LIBRARY_READ = "user-library-read"
    USER_LIBRARY_MODIFY = "user-library-modify"
    USER_TOP_READ = "user-top-read"
    USER_READ_RECENTLY_PLAYED = "user-read-recently-played"
    PLAYLIST_MODIFY_PUBLIC = "playlist-modify-public"
    PLAYLIST_MODIFY_PRIVATE = "playlist-modify-private"
    PLAYLIST_READ_PRIVATE = "playlist-read-private"
