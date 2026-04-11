from __future__ import annotations

from enum import StrEnum
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field


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


class SpotifyView(BaseModel):
    model_config = ConfigDict(extra="allow")


class OperationResult(SpotifyView):
    success: bool = True
    snapshot_id: str | None = None
    raw: dict[str, Any] | None = None


class PlaybackOptions(SpotifyView):
    repeat_state: Literal["track", "context", "off"] | None = None
    shuffle_state: bool | None = None
    volume_percent: int | None = Field(default=None, ge=0, le=100)
