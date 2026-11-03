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

## HTTP transport

The API and OAuth clients now use `httpx2>=2.16.0,<3`. Applications that inject
`transport=` into `SpotifyClient`, `SpotifyAPIClient` or `SpotifyOAuth` must
construct it from `httpx2`, for example `httpx2.AsyncHTTPTransport()` or
`httpx2.MockTransport(handler)`. Custom transports should subclass
`httpx2.AsyncBaseTransport`. `RetryEvent.response` is now an `httpx2.Response`;
underlying transport exceptions also come from `httpx2`. The SDK's public
exception classes remain the same.

HTTPX2 uses the operating system's certificate store by default and still honors
`SSL_CERT_FILE` and `SSL_CERT_DIR`. Its logger names are `httpx2` and `httpcore2.*`,
and its default User-Agent is `python-httpx2/<version>`. See the
[upstream migration guide](https://pydantic.dev/docs/httpx2/get-started/migration/)
for details. HTTPX and HTTPX2 objects belong to separate class hierarchies.

## Explicit login

API calls no longer open browsers or prompt. Before user-scoped operations,
supply a user access/refresh token or use `SpotifyOAuth.authorization_url()` and
`exchange_code()` with the required scopes. See the
[Python authorization example](../README.md#user-authorization) for a loopback
login flow. Use an explicit redirect such as `http://127.0.0.1:8888/callback`.

Select an account with `SpotifyClient(cache_profile="work")` and the matching
`CacheFileHandler(client_id=..., profile="work")` during authorization.

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

## CLI removal

The optional CLI, its `spotifyify` console command and the `[cli]` extra have
been removed. Use the Python client for API calls and the OAuth helpers above
for authorization. Serialize response models with
`model.model_dump(mode="json", exclude_unset=True)` when JSON output is needed.
