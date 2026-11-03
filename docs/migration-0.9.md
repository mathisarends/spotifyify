# Migrating from 0.8 to 0.9

## Public names

Use `from spotifyify import SpotifyClient`. `Spotifyify` remains an alias for
existing integrations. The low-level client is `SpotifyAPIClient`; imports of
`spotifyify.client.SpotifyClient` retain their old low-level meaning. The OAuth
provider is `spotifyify.oauth2.SpotifyOAuth`, and the base exception is
`SpotifyError`. Their previous names remain aliases.

`search()` replaces `find()`, and `playlists.items()` replaces
`playlists.tracks()`. The old methods remain aliases. `request_context()` names
the per-request token/retry context; `session()` still works. Use `aclose()` for
explicit cleanup; `close()` remains an async alias. Closed clients cannot reopen.

## Explicit login

API calls no longer open browsers or prompt. Before user-scoped operations:

```bash
spotifyify auth login --scope user-library-read --scope user-library-modify
spotifyify auth login --scope user-follow-read --scope user-follow-modify
```

Login preserves previously granted scopes for the selected profile. Select an
account with `spotifyify --profile work ...` or `SPOTIFYIFY_PROFILE=work`.
Use an explicit loopback redirect such as `http://127.0.0.1:8888/callback`.

Tokens are no longer written into the working directory or back into
`SpotifyCredentials`. Default cache files are separated by client ID and profile
in the user's application data/cache directory. Log in again to populate the new
location, or explicitly pass `CacheFileHandler(".cache")` for an existing cache.
Legacy records without a known user grant require a fresh login.

Environment access tokens with unknown expiry/scopes are sent as supplied;
Spotify enforces their validity. `SPOTIFY_TOKEN_EXPIRES_AT` and
`SPOTIFY_TOKEN_SCOPES` supply known metadata. Refresh tokens still need app
credentials. Invalid grants are discarded instead of retried on every request.

## Spotify API mode

The default is `api_mode="development"`, matching the current Development Mode
contract. Select `api_mode="extended"` only if the app has Extended Quota access.
The CLI accepts `--api-mode extended` or `SPOTIFYIFY_API_MODE=extended`.

Development Mode uses generic library URI operations, creates playlists through
`/me/playlists`, and performs bounded individual reads for `get_many()`. Removed
browse/artist/other-user operations fail with `SpotifyUnsupportedOperation`.
Search accepts at most 10 results per request in this mode; use pagination.

`get_many()` now preserves missing positions as `None`. Check each entry before
using its attributes. Playlist `items` and nested `item` are canonical model
fields; legacy attributes and server responses remain supported. Field-filtered
playlist pages return `PlaylistProjection` instead of a complete paging model.

## Failures and multi-request writes

Catch `SpotifyError` to handle all expected SDK failures. Network and malformed
response failures use `SpotifyTransportError` and `SpotifyResponseError`.
Ambiguous playlist reorders are not retried. Retries have capped backoff, jitter,
a configurable maximum wait, and a shared client cooldown for rate limits.

Large playlist writes can partially apply. `SpotifyBatchError` exposes the
processed input count and last snapshot; do not blindly repeat completed batches.
Inputs are validated before authentication or HTTP requests.

## CLI output

`playlists items` replaces the visible `playlists tracks` command. The old command
is a hidden alias. Paged commands accept `--all`, and offset-based commands also
accept `--offset`. The SDK owns batching for both Python and CLI callers.

Use `--full` or `SPOTIFYIFY_FULL=1` for complete normalized models.
`SPOTIFYIFY_RAW=1` remains a legacy alias. Full output retains unknown fields and
explicit nulls, but normalizes model aliases/types and combines requested pages;
it is not a byte-for-byte HTTP response.
