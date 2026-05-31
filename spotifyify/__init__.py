import logging

from .spotifyify import Spotifyify
from .credentials import SpotifyCredentials
from .oauth2 import SpotifyScope
from .schemas import (
    # Core models
    Track,
    Album,
    Artist,
    Playlist,
    Episode,
    Show,
    Device,
    PlaybackState,
    PlayerQueue,
    AudioFeatures,
    AudioAnalysis,
    User,
    PublicUser,
    Image,
    ExternalUrl,
    Followers,
    Context,
    Category,
    PlaylistTrack,
    # Simplified models
    SimplifiedTrack,
    SimplifiedAlbum,
    SimplifiedArtist,
    SimplifiedPlaylist,
    SimplifiedEpisode,
    SimplifiedShow,
    ArtistDiscographyAlbum,
    # Saved-item wrappers
    SavedTrack,
    SavedAlbum,
    SavedShow,
    SavedEpisode,
    # Compound models
    PlayHistory,
    Recommendations,
    # Paging bases
    Paging,
    CursorPaging,
    # Typed paging
    PagingTrack,
    PagingArtist,
    PagingPlaylist,
    PagingPlaylistTrack,
    PagingSimplifiedTrack,
    PagingSimplifiedAlbum,
    PagingSimplifiedEpisode,
    PagingSimplifiedShow,
    PagingArtistDiscographyAlbum,
    PagingSavedTrack,
    PagingSavedAlbum,
    PagingSavedShow,
    PagingSavedEpisode,
    CursorPagingPlayHistory,
    CursorPagingSimplifiedArtist,
)


__all__ = [
    # Client & config
    "Spotifyify",
    "SpotifyCredentials",
    "SpotifyScope",
    # Core models
    "Track",
    "Album",
    "Artist",
    "Playlist",
    "Episode",
    "Show",
    "Device",
    "PlaybackState",
    "PlayerQueue",
    "AudioFeatures",
    "AudioAnalysis",
    "User",
    "PublicUser",
    "Image",
    "ExternalUrl",
    "Followers",
    "Context",
    "Category",
    "PlaylistTrack",
    # Simplified models
    "SimplifiedTrack",
    "SimplifiedAlbum",
    "SimplifiedArtist",
    "SimplifiedPlaylist",
    "SimplifiedEpisode",
    "SimplifiedShow",
    "ArtistDiscographyAlbum",
    # Saved-item wrappers
    "SavedTrack",
    "SavedAlbum",
    "SavedShow",
    "SavedEpisode",
    # Compound models
    "PlayHistory",
    "Recommendations",
    # Paging bases
    "Paging",
    "CursorPaging",
    # Typed paging
    "PagingTrack",
    "PagingArtist",
    "PagingPlaylist",
    "PagingPlaylistTrack",
    "PagingSimplifiedTrack",
    "PagingSimplifiedAlbum",
    "PagingSimplifiedEpisode",
    "PagingSimplifiedShow",
    "PagingArtistDiscographyAlbum",
    "PagingSavedTrack",
    "PagingSavedAlbum",
    "PagingSavedShow",
    "PagingSavedEpisode",
    "CursorPagingPlayHistory",
    "CursorPagingSimplifiedArtist",
]

logging.getLogger(__name__).addHandler(logging.NullHandler())
