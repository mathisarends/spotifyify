# Changelog

## 0.9.0 (2026-11-03)

### Breaking changes

- Remove the optional CLI, the `spotifyify` console command and the `[cli]` extra.
  Use the async Python client and explicit OAuth helpers instead.
- Use HTTPX2 (`httpx2>=2.16.0,<3`) for API and OAuth requests. Injected transports,
  response type checks and underlying transport exceptions must use HTTPX2 types.
- Default to Spotify's Development Mode contract. Apps with Extended Quota
  access can select `api_mode="extended"`; this does not grant quota access.
- Require explicit user authorization before user-scoped calls. Tokens are
  cached per client ID and profile in the user's application data/cache directory,
  rather than automatically reading a project-local cache.
- Preserve missing `get_many()` results as `None` in input order. Canonical
  playlist model fields are `items`/`item`; field-filtered pages return
  `PlaylistProjection`.

### Added and improved

- Expose `SpotifyClient`, `SpotifyAPIClient` and `SpotifyError` as the preferred
  public names. Keep compatibility aliases including `Spotifyify`, `find()`,
  `playlists.tracks()`, `session()` and async `close()`.
- Isolate request tokens and retry hooks per client and async task through
  `request_context()`. Support caller-owned token providers and injectable HTTP
  transports; the client closes its HTTP transport during cleanup.
- Serialize refreshes, preserve token grants, discard revoked grants and write
  token caches atomically. Provide explicit loopback OAuth callback helpers.
- Validate inputs before authentication, paginate lazily and batch large reads
  and playlist writes. Report partial writes through `SpotifyBatchError`.
- Guard unsafe retries, cap backoff and retry waits, and share rate-limit cooldowns
  across requests on one client. Normalize transport and malformed-response errors.
- Maintain typed resource models with `py.typed`, legacy playlist aliases and
  a pinned OpenAPI source. Reject complete pages without an item collection.
- Validate Python and MCP examples and run CI on Windows and Linux with Python
  3.13 and 3.14, including linting, formatting, type checking and distribution builds.

See the [migration guide](docs/migration-0.9.md) before upgrading and the
[release checklist](docs/releasing.md) for publication steps.
