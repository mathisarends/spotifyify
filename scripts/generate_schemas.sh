#!/bin/bash
set -e

SPEC_URL="https://developer.spotify.com/reference/web-api/open-api-schema.yaml"
SPEC_FILE="specs/spotify.openapi.yml"
OUTPUT_FILE="spotifyify/schemas.py"
PACKAGE_INIT_FILE="spotifyify/__init__.py"

echo "Fetching Spotify OpenAPI spec..."
mkdir -p specs
curl -L -o "$SPEC_FILE" "$SPEC_URL"

echo "Generating Pydantic v2 schemas into $OUTPUT_FILE..."
uvx --from datamodel-code-generator datamodel-codegen \
  --input "$SPEC_FILE" \
  --input-file-type openapi \
  --output "$OUTPUT_FILE" \
  --output-model-type pydantic_v2.BaseModel

echo "Applying schema compatibility patch for nullable paging links..."
python - << 'PY'
from pathlib import Path

path = Path("spotifyify/schemas.py")
content = path.read_text(encoding="utf-8")

marker = "class PagingObject(BaseModel):"
start = content.find(marker)
if start == -1:
  raise RuntimeError("PagingObject not found in generated schemas")

next_class = content.find("\n\nclass ", start + len(marker))
if next_class == -1:
  next_class = len(content)

block = content[start:next_class]
updated = block
updated = updated.replace("next: str = Field(", "next: str | None = Field(")
updated = updated.replace("previous: str = Field(", "previous: str | None = Field(")
updated = updated.replace("next: str | None = Field(\n        ...,", "next: str | None = Field(\n        None,")
updated = updated.replace("previous: str | None = Field(\n        ...,", "previous: str | None = Field(\n        None,")

if block == updated:
  raise RuntimeError("PagingObject patch did not apply; generator output changed")

path.write_text(content[:start] + updated + content[next_class:], encoding="utf-8")
PY

echo "Appending convenience aliases..."
cat >> "$OUTPUT_FILE" << 'ALIASES'

# ---------------------------------------------------------------------------
# Convenience aliases - drop the verbose "Object" suffix
# ---------------------------------------------------------------------------

# Core models
Track = TrackObject
Album = AlbumObject
Artist = ArtistObject
Playlist = PlaylistObject
Episode = EpisodeObject
Show = ShowObject
Device = DeviceObject
PlaybackState = CurrentlyPlayingContextObject
PlayerQueue = QueueObject
AudioFeatures = AudioFeaturesObject
AudioAnalysis = AudioAnalysisObject
User = PrivateUserObject
PublicUser = PublicUserObject
Image = ImageObject
ExternalUrl = ExternalUrlObject
ExternalId = ExternalIdObject
Followers = FollowersObject
Copyright = CopyrightObject
Context = ContextObject
LinkedTrack = LinkedTrackObject
Category = CategoryObject
Audiobook = AudiobookObject
Chapter = ChapterObject
PlaylistTrack = PlaylistTrackObject

# Simplified models
SimplifiedTrack = SimplifiedTrackObject
SimplifiedAlbum = SimplifiedAlbumObject
SimplifiedArtist = SimplifiedArtistObject
SimplifiedPlaylist = SimplifiedPlaylistObject
SimplifiedEpisode = SimplifiedEpisodeObject
SimplifiedShow = SimplifiedShowObject
SimplifiedAudiobook = SimplifiedAudiobookObject
SimplifiedChapter = SimplifiedChapterObject
ArtistDiscographyAlbum = ArtistDiscographyAlbumObject

# Saved-item wrappers
SavedTrack = SavedTrackObject
SavedAlbum = SavedAlbumObject
SavedShow = SavedShowObject
SavedEpisode = SavedEpisodeObject

# Other compound models
PlayHistory = PlayHistoryObject
Recommendations = RecommendationsObject
Error = ErrorObject

# Paging helpers (generic bases)
Paging = PagingObject
CursorPaging = CursorPagingObject

# Typed paging models
PagingTrack = PagingTrackObject
PagingArtist = PagingArtistObject
PagingPlaylist = PagingPlaylistObject
PagingPlaylistTrack = PagingPlaylistTrackObject
PagingSimplifiedTrack = PagingSimplifiedTrackObject
PagingSimplifiedAlbum = PagingSimplifiedAlbumObject
PagingSimplifiedEpisode = PagingSimplifiedEpisodeObject
PagingSimplifiedShow = PagingSimplifiedShowObject
PagingSimplifiedAudiobook = PagingSimplifiedAudiobookObject
PagingSimplifiedChapter = PagingSimplifiedChapterObject
PagingArtistDiscographyAlbum = PagingArtistDiscographyAlbumObject
PagingSavedTrack = PagingSavedTrackObject
PagingSavedAlbum = PagingSavedAlbumObject
PagingSavedShow = PagingSavedShowObject
PagingSavedEpisode = PagingSavedEpisodeObject
CursorPagingPlayHistory = CursorPagingPlayHistoryObject
CursorPagingSimplifiedArtist = CursorPagingSimplifiedArtistObject
ALIASES

echo "Writing package re-exports to $PACKAGE_INIT_FILE..."
cat > "$PACKAGE_INIT_FILE" << 'PACKAGE_INIT'
from .spotifyify import Spotifyify
from .credentials import SpotifyCredentials
from .scopes import SpotifyScope
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
PACKAGE_INIT

echo "Done! Schemas generated in $OUTPUT_FILE and re-exports updated in $PACKAGE_INIT_FILE"
