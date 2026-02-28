from enum import StrEnum
from typing import Literal

from pydantic import BaseModel, Field


class SpotifyScope(StrEnum):
    USER_READ_PLAYBACK_STATE = (
        "user-read-playback-state"  # current_playback(), devices()
    )
    USER_MODIFY_PLAYBACK_STATE = "user-modify-playback-state"  # start_playback(), add_to_queue(), volume(), transfer_playback()
    USER_LIBRARY_READ = "user-library-read"  # current_user_saved_tracks(), current_user_saved_tracks_contains()
    USER_LIBRARY_MODIFY = "user-library-modify"  # current_user_saved_tracks_add(), current_user_saved_tracks_delete()
    USER_TOP_READ = "user-top-read"  # current_user_top_tracks()
    USER_READ_RECENTLY_PLAYED = (
        "user-read-recently-played"  # current_user_recently_played()
    )
    PLAYLIST_MODIFY_PUBLIC = "playlist-modify-public"  # Create/modify public playlists
    PLAYLIST_MODIFY_PRIVATE = (
        "playlist-modify-private"  # Create/modify private playlists
    )


class ActionSuccessResponse(BaseModel):
    status: Literal["success"] = Field(
        default="success", description="Status of the action"
    )
    message: str = Field(description="Human-readable message about the action result")
