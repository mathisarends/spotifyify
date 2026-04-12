#!/bin/bash
set -e

SPEC_URL="https://developer.spotify.com/reference/web-api/open-api-schema.yaml"
SPEC_FILE=".specs/spotify.openapi.yml"
OUTPUT_DIR="spotifyify/schemas"

echo "Fetching Spotify OpenAPI spec..."
mkdir -p .specs
curl -L -o "$SPEC_FILE" "$SPEC_URL"

echo "Generating Pydantic v2 schemas into $OUTPUT_DIR..."
uvx --from datamodel-code-generator datamodel-codegen \
  --input "$SPEC_FILE" \
  --input-file-type openapi \
  --output "$OUTPUT_DIR" \
  --output-model-type pydantic_v2.BaseModel

echo "Appending convenience aliases..."
cat >> "$OUTPUT_DIR/__init__.py" << 'ALIASES'

# ---------------------------------------------------------------------------
# Convenience aliases used by the namespace API layer
# ---------------------------------------------------------------------------
Track = TrackObject
Album = AlbumObject
Artist = ArtistObject
Playlist = PlaylistObject
SimplifiedPlaylist = SimplifiedPlaylistObject
Episode = EpisodeObject
SimplifiedEpisode = SimplifiedEpisodeObject
Show = ShowObject
SimplifiedShow = SimplifiedShowObject
Device = DeviceObject
PlaybackState = CurrentlyPlayingContextObject
PlayerQueue = QueueObject
Paging = PagingObject
CursorPaging = CursorPagingObject
AudioFeatures = AudioFeaturesObject
AudioAnalysis = AudioAnalysisObject
User = PrivateUserObject
PublicUser = PublicUserObject
SavedTrack = SavedTrackObject
SavedAlbum = SavedAlbumObject
SavedShow = SavedShowObject
SavedEpisode = SavedEpisodeObject
PlayHistory = PlayHistoryObject
Recommendations = RecommendationsObject
ALIASES

echo "Done! Schemas generated in $OUTPUT_DIR"
