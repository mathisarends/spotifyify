from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class SpotifyModel(BaseModel):
    model_config = ConfigDict(extra="allow", populate_by_name=True)


class Image(SpotifyModel):
    url: str
    width: int | None = None
    height: int | None = None


class Artist(SpotifyModel):
    id: str | None = None
    name: str
    uri: str | None = None
    href: str | None = None


class Album(SpotifyModel):
    id: str
    name: str
    uri: str
    album_type: str | None = None
    artists: list[Artist] = Field(default_factory=list)
    images: list[Image] = Field(default_factory=list)


class Track(SpotifyModel):
    id: str | None = None
    name: str
    uri: str | None = None
    duration_ms: int | None = None
    explicit: bool | None = None
    artists: list[Artist] = Field(default_factory=list)
    album: Album | None = None


class Episode(SpotifyModel):
    id: str | None = None
    name: str
    uri: str | None = None
    duration_ms: int | None = None
    explicit: bool | None = None
    images: list[Image] = Field(default_factory=list)


class Show(SpotifyModel):
    id: str
    name: str
    uri: str | None = None
    publisher: str | None = None
    images: list[Image] = Field(default_factory=list)


class Device(SpotifyModel):
    id: str | None = None
    is_active: bool
    is_private_session: bool
    is_restricted: bool
    name: str
    type: str
    volume_percent: int | None = None


class Playlist(SpotifyModel):
    id: str
    name: str
    uri: str
    description: str | None = None
    public: bool | None = None
    collaborative: bool | None = None
    images: list[Image] = Field(default_factory=list)


class Queue(SpotifyModel):
    currently_playing: Track | Episode | None = None
    queue: list[Track | Episode] = Field(default_factory=list)


class Paging(SpotifyModel):
    href: str | None = None
    limit: int | None = None
    next: str | None = None
    offset: int | None = None
    previous: str | None = None
    total: int | None = None
    items: list[Any] = Field(default_factory=list)


class SearchResult(SpotifyModel):
    tracks: Paging | None = None
    albums: Paging | None = None
    artists: Paging | None = None
    playlists: Paging | None = None
    shows: Paging | None = None
    episodes: Paging | None = None


class PlaybackState(SpotifyModel):
    device: Device | None = None
    shuffle_state: bool | None = None
    repeat_state: str | None = None
    timestamp: int | None = None
    progress_ms: int | None = None
    is_playing: bool | None = None
    item: Track | Episode | None = None


class CurrentlyPlaying(SpotifyModel):
    timestamp: int | None = None
    progress_ms: int | None = None
    is_playing: bool | None = None
    currently_playing_type: str | None = None
    item: Track | Episode | None = None
