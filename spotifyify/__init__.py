import logging

from .auth import AccessTokenProvider
from .client import SpotifyAPIClient
from .config import ApiMode
from .credentials import SpotifyCredentials
from .exceptions import (
    SpotifyAPIError,
    SpotifyAuthError,
    SpotifyBatchError,
    SpotifyError,
    SpotifyifyError,
    SpotifyRateLimitError,
    SpotifyResponseError,
    SpotifyTransportError,
    SpotifyUnsupportedOperation,
)
from .http import OnRetryHook, RetryEvent, RetryPolicy
from .oauth2 import SpotifyScope
from .schemas import (
    Album,
    Artist,
    ArtistDiscographyAlbum,
    AudioAnalysis,
    Category,
    Context,
    CursorPaging,
    CursorPagingPlayHistory,
    CursorPagingSimplifiedArtist,
    Device,
    Episode,
    ExternalUrl,
    Followers,
    Image,
    # Paging bases
    Paging,
    PagingArtist,
    PagingArtistDiscographyAlbum,
    PagingPlaylist,
    PagingPlaylistItem,
    PagingPlaylistTrack,
    PagingSavedAlbum,
    PagingSavedEpisode,
    PagingSavedShow,
    PagingSavedTrack,
    PagingSimplifiedAlbum,
    PagingSimplifiedEpisode,
    PagingSimplifiedShow,
    PagingSimplifiedTrack,
    # Typed paging
    PagingTrack,
    PlaybackState,
    PlayerQueue,
    # Compound models
    PlayHistory,
    Playlist,
    PlaylistItem,
    PlaylistProjection,
    PlaylistTrack,
    PublicUser,
    SavedAlbum,
    SavedEpisode,
    SavedShow,
    # Saved-item wrappers
    SavedTrack,
    Show,
    SimplifiedAlbum,
    SimplifiedArtist,
    SimplifiedEpisode,
    SimplifiedPlaylist,
    SimplifiedShow,
    # Simplified models
    SimplifiedTrack,
    # Core models
    Track,
    User,
)
from .spotify import SpotifyClient
from .spotifyify import Spotifyify

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
