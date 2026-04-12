#!/bin/bash
set -e

SPEC_URL="https://developer.spotify.com/reference/web-api/open-api-schema.yaml"
SPEC_FILE="openapi.yml"
OUTPUT_DIR="spotifyify/schemas"

echo "Fetching Spotify OpenAPI spec..."
curl -L -o "$SPEC_FILE" "$SPEC_URL"

echo "Generating Pydantic v2 schemas into $OUTPUT_DIR..."
uvx --from datamodel-code-generator datamodel-codegen \
  --input "$SPEC_FILE" \
  --input-file-type openapi \
  --output "$OUTPUT_DIR" \
  --output-model-type pydantic_v2.BaseModel

echo "Done! Schemas generated in $OUTPUT_DIR"
