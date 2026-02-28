from datetime import datetime
from pydantic import BaseModel, Field


class SimplifiedArtist(BaseModel):
    id: str
    name: str


class SimplifiedAlbum(BaseModel):
    id: str
    name: str
    uri: str
    artists: list[SimplifiedArtist] = Field(default_factory=list)


class Track(BaseModel):
    id: str
    name: str
    uri: str
    artists: list[SimplifiedArtist] = Field(default_factory=list)
    duration_ms: int
    album: SimplifiedAlbum | None = None


class Device(BaseModel):
    id: str
    name: str
    is_active: bool
    volume_percent: int | None = None


class PlaybackState(BaseModel):
    is_playing: bool
    progress_ms: int | None = None
    device: Device
    item: Track | None = None


class DevicesResponse(BaseModel):
    devices: list[Device] = Field(default_factory=list)


class PagingObject(BaseModel):
    total: int
    limit: int
    offset: int


class RecentlyPlayedTrack(BaseModel):
    track: Track
    played_at: datetime


class RecentlyPlayedResponse(BaseModel):
    items: list[RecentlyPlayedTrack] = Field(default_factory=list)
    limit: int


class TracksSearchResult(PagingObject):
    items: list[Track] = Field(default_factory=list)


class AlbumsSearchResult(PagingObject):
    items: list[SimplifiedAlbum] = Field(default_factory=list)


class SearchResponse(BaseModel):
    tracks: TracksSearchResult | None = None
    albums: AlbumsSearchResult | None = None


class Artist(BaseModel):
    id: str
    name: str
    uri: str
    images: list[dict] = Field(default_factory=list)
    genres: list[str] = Field(default_factory=list)
    popularity: int | None = None
    followers: dict | None = None


class Album(BaseModel):
    id: str
    name: str
    uri: str
    artists: list[SimplifiedArtist] = Field(default_factory=list)
    images: list[dict] = Field(default_factory=list)
    release_date: str | None = None
    total_tracks: int | None = None


class AlbumDetails(Album):
    tracks: list[Track] = Field(default_factory=list)


class AlbumTracksResponse(BaseModel):
    items: list[Track] = Field(default_factory=list)
    limit: int
    offset: int
    total: int


class Playlist(BaseModel):
    id: str
    name: str
    uri: str
    description: str | None = None
    public: bool | None = None
    owner: dict | None = None
    images: list[dict] = Field(default_factory=list)


class PlaylistsResponse(BaseModel):
    items: list[Playlist] = Field(default_factory=list)
    limit: int
    offset: int
    total: int


class Show(BaseModel):
    id: str
    name: str
    uri: str
    description: str | None = None
    images: list[dict] = Field(default_factory=list)
    publisher: str | None = None
    total_episodes: int | None = None


class Episode(BaseModel):
    id: str
    name: str
    uri: str
    description: str | None = None
    release_date: str | None = None
    duration_ms: int | None = None
    show: Show | None = None


class ShowsSearchResult(PagingObject):
    items: list[Show] = Field(default_factory=list)


class EpisodesResponse(BaseModel):
    items: list[Episode] = Field(default_factory=list)
    limit: int
    offset: int
    total: int


class SavedTracksResponse(BaseModel):
    items: list[Track] = Field(default_factory=list)
    limit: int
    offset: int
    total: int


class ArtistsSearchResult(PagingObject):
    items: list[Artist] = Field(default_factory=list)


class TopTracksResponse(BaseModel):
    items: list[Track] = Field(default_factory=list)
    total: int
    limit: int


class TopArtistsResponse(BaseModel):
    items: list[Artist] = Field(default_factory=list)
    total: int
    limit: int


class QueueResponse(BaseModel):
    currently_playing: Track | None = None
    queue: list[Track] = Field(default_factory=list)


class SavedShow(BaseModel):
    added_at: datetime
    show: Show


class SavedShowsResponse(BaseModel):
    items: list[SavedShow] = Field(default_factory=list)
    limit: int
    offset: int
    total: int


class SavedAlbum(BaseModel):
    added_at: datetime
    album: SimplifiedAlbum


class SavedAlbumsResponse(BaseModel):
    items: list[SavedAlbum] = Field(default_factory=list)
    limit: int
    offset: int
    total: int


class NewReleasesResponse(BaseModel):
    albums: list[SimplifiedAlbum] = Field(default_factory=list)
    total: int
    limit: int
    offset: int


class CurrentlyPlayingResponse(BaseModel):
    is_playing: bool
    progress_ms: int | None = None
    item: Track | None = None
