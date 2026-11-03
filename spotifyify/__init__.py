import logging

from .spotifyify import Spotifyify
from .spotify import SpotifyClient
from .client import SpotifyAPIClient
from .auth import AccessTokenProvider
from .config import ApiMode
from .credentials import SpotifyCredentials
from .exceptions import (
    SpotifyAPIError,
    SpotifyAuthError,
    SpotifyError,
    SpotifyifyError,
    SpotifyRateLimitError,
    SpotifyResponseError,
    SpotifyTransportError,
    SpotifyUnsupportedOperation,
    SpotifyBatchError,
)
from .oauth2 import SpotifyScope
from .http import OnRetryHook, RetryEvent, RetryPolicy
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
    AudioAnalysis,
    User,
    PublicUser,
    Image,
    ExternalUrl,
    Followers,
    Context,
    Category,
    PlaylistTrack,
    PlaylistItem,
    PagingPlaylistItem,
    PlaylistProjection,
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
    "SpotifyClient",
    "SpotifyAPIClient",
    "AccessTokenProvider",
    "ApiMode",
    "SpotifyError",
    "SpotifyifyError",
    "SpotifyCredentials",
    "SpotifyScope",
    "OnRetryHook",
    "RetryEvent",
    "RetryPolicy",
    "SpotifyAPIError",
    "SpotifyAuthError",
    "SpotifyRateLimitError",
    "SpotifyResponseError",
    "SpotifyTransportError",
    "SpotifyUnsupportedOperation",
    "SpotifyBatchError",
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
    "AudioAnalysis",
    "User",
    "PublicUser",
    "Image",
    "ExternalUrl",
    "Followers",
    "Context",
    "Category",
    "PlaylistTrack",
    "PlaylistItem",
    "PagingPlaylistItem",
    "PlaylistProjection",
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
