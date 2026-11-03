# Response model maintenance

The public response models are maintained in `spotifyify/models/`, grouped by
resource. `spotifyify.schemas` preserves the previous imports. They are a curated
SDK interface, rather than unmodified generator output.

`schemas/spotify.openapi.yaml.gz` pins the official Spotify OpenAPI source.
`schemas/source.json` records its URL, retrieval date, SHA-256 checksum, generator
version, and generator options. The compressed input is checked in, so generation
does not fetch a changing upstream URL.

Generate a separate upstream baseline for comparison:

```bash
uv run --group schema python tools/generate_models.py
uv run python tools/generate_models.py --verify-only
```

The default baseline is `build/spotify-schema-baseline.py`. Public models are
deliberately not overwritten: generic paging, stable names, aliases, and
Development/Extended Quota compatibility are maintained adaptations. Review an
updated baseline, port relevant changes to the resource modules, and add payload
regressions to `tests/test_response_models.py` before updating the pinned source.

Compatibility rules:

- Both legacy `tracks`/`track` and current `items`/`item` playlist fields are
  accepted. Public serialization uses `items`/`item`; old attributes still work.
- Fields removed from Development Mode are optional. Unknown fields are kept.
- Full output serializes the models; it is not a byte-for-byte HTTP response.
  Explicit nulls and unknown fields survive, but aliases and timestamps normalize.
- Server-side playlist field filters return `PlaylistProjection`, whose selected
  fields do not require full paging metadata or an item discriminator.
- `Paging[T]` and `CursorPaging[T]` share the page contract. Existing specialized
  paging classes and imports remain available.
