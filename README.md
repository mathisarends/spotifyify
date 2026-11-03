# spotifyify

An async-first Spotify client built on HTTPX2, with a namespaced API and fully typed response models maintained in the codebase and aligned with the [official Spotify OpenAPI specification](https://developer.spotify.com/reference/web-api/open-api-schema.yaml).

See [the 0.9 migration guide](docs/migration-0.9.md) for renamed APIs, explicit
login, API modes and output changes. `Spotifyify` remains a compatibility alias.

## Requirements

- Python 3.13+
- A Spotify app registered at [developer.spotify.com](https://developer.spotify.com/dashboard)
- Development Mode requires an active Premium subscription for the app owner;
  see [Spotify's API-mode requirements](https://developer.spotify.com/documentation/web-api/tutorials/february-2026-migration-guide).

## Installation

```bash
pip install spotifyify
```

With [uv](https://github.com/astral-sh/uv):

```bash
uv add spotifyify
```

## Configuration

Credentials are loaded from environment variables (or a `.env` file via `pydantic-settings`):

| Variable                   | Required      | Description                           |
| -------------------------- | ------------- | ------------------------------------- |
| `SPOTIFY_CLIENT_ID`        | App auth/refresh           | Your app's client ID                  |
| `SPOTIFY_CLIENT_SECRET`    | App auth/refresh           | Your app's client secret              |
| `SPOTIFY_REDIRECT_URI`     | For user auth | OAuth redirect URI                    |
| `SPOTIFY_ACCESS_TOKEN`     | Optional      | Pre-existing access token             |
| `SPOTIFY_REFRESH_TOKEN`    | Optional      | Refresh token for automatic renewal   |
| `SPOTIFY_TOKEN_EXPIRES_AT` | Optional      | Unix timestamp when the token expires |
| `SPOTIFY_TOKEN_SCOPES`     | Optional      | Known space-separated token scopes |

**.env example:**

```env
SPOTIFY_CLIENT_ID=your_client_id
SPOTIFY_CLIENT_SECRET=your_client_secret
SPOTIFY_REDIRECT_URI=http://127.0.0.1:8888/callback
SPOTIFY_REFRESH_TOKEN=your_refresh_token
```

If `SPOTIFY_REFRESH_TOKEN` (or `SPOTIFY_ACCESS_TOKEN`) is present the client operates in user mode. Without them it falls back to the [Client Credentials flow](https://developer.spotify.com/documentation/web-api/tutorials/client-credentials-flow), which only allows access to public data.

### User authorization

User-scoped calls require an existing user grant. API calls never open a browser
or prompt for input. Supply a user access/refresh token through the environment,
or authorize explicitly with the Python OAuth helpers:

```python
import asyncio
import secrets
import webbrowser

from spotifyify import SpotifyCredentials
from spotifyify.cache_handler import CacheFileHandler
from spotifyify.oauth2 import SpotifyOAuth
from spotifyify.oauth2.callback import capture_local_code

async def login():
    credentials = SpotifyCredentials()
    if not credentials.redirect_uri:
        raise ValueError("Set SPOTIFY_REDIRECT_URI before authorizing")
    cache = CacheFileHandler(client_id=credentials.client_id, profile="default")
    oauth = SpotifyOAuth(credentials, cache)
    try:
        state = secrets.token_urlsafe(32)
        scopes = ["user-read-playback-state", "user-modify-playback-state"]
        url = oauth.authorization_url(state=state, scope=scopes)
        code = await capture_local_code(
            credentials.redirect_uri,
            state=state,
            on_ready=lambda: webbrowser.open(url),
        )
        await oauth.exchange_code(code, scope=scopes)
    finally:
        await oauth.close()

asyncio.run(login())
```

Configure an explicit loopback redirect such as
`http://127.0.0.1:8888/callback` for this example. The listener starts before the
browser opens. Applications with their own callback handler can validate the
redirect with `parse_callback_url()` and pass the code to `exchange_code()`.

Use the same profile in `CacheFileHandler(profile="work", ...)` and
`SpotifyClient(cache_profile="work")` to keep accounts separate. Tokens are cached
per client ID and profile under the user's application data directory on Windows
or `$XDG_CACHE_HOME/spotifyify` on Unix. Cache files are written atomically, with
owner-only permissions on Unix and inherited user-profile ACLs on Windows. They
contain unencrypted credentials. Existing project-local caches can be selected
explicitly with `CacheFileHandler(".cache")`; the client does not import them
automatically.

### Bring your own user token

Multi-user backends can pass an already minted end-user access token for one request scope. While the context is active, spotifyify sends that token directly and skips its configured OAuth provider, app credentials, cache, refresh, and scope checks. Expired or insufficient tokens surface as Spotify API errors.

The token context is isolated per client instance and async task, so one shared `SpotifyClient` instance can serve concurrent users:

```python
async with SpotifyClient() as spotify:
    async with spotify.request_context(access_token=end_user_access_token):
        playlist = await spotify.playlists.create("Weekly Mix", public=False)
        await spotify.playlists.replace(
            playlist.id,
            ["spotify:track:...", "spotify:track:..."],
        )
```

## Quick start

```python
import asyncio
from spotifyify import SpotifyClient, SpotifyScope

async def main():
    async with SpotifyClient(scopes=[SpotifyScope.USER_READ_PLAYBACK_STATE]) as sp:
        state = await sp.player.state()
        if state and state.item:
            print(f"Now playing: {state.item.name}")

asyncio.run(main())
```

## API design

The default API contract is Spotify **Development Mode** (including the 2026
changes). Library writes/checks use `/me/library`, playlists are created with
`/me/playlists`, and `get_many()` uses bounded individual reads. Search accepts
at most 10 items per request in this mode. Endpoints Spotify removed from this
mode fail locally with `SpotifyUnsupportedOperation`.

Apps that already have Extended Quota access can select the legacy-compatible
contract with `SpotifyClient(api_mode="extended")`.
This option selects endpoints; it does not change the app's Spotify quota mode.

`get_many()` accepts any number of IDs, batches where supported, and returns one
entry per input ID in the same order. Missing entries are `None`. Configure
parallel read workers with `concurrency` (default: 8). Empty input returns an
empty list; pass `[track_id]` for one ID rather than a plain string.

Use `iter_search()`, `library.iter_saved_tracks()` (and the corresponding album,
show and episode iterators), `playlists.iter_items()`, `users.iter_following()` or
`player.iter_recently_played()` to consume pages lazily:

```python
async for saved in spotify.library.iter_saved_tracks(limit=50):
    print(saved.track.name)
```

Playlist `add()`, `remove()` and `replace()` split large writes into ordered
requests. These operations are not atomic across requests. If a later request
fails, `SpotifyBatchError` exposes `completed_items`, `total_items` and the last
`snapshot_id`; its cause retains the underlying error. Counts refer to processed
input URIs, not the number of playlist entries removed. Restarting the whole
operation can duplicate already applied changes, so recover using that progress.

The `SpotifyClient` class is the entry point. It exposes all Spotify resources as lazy-loaded namespace properties. Request methods are awaited; iter_* methods are consumed with async for.

```
SpotifyClient
├── .tracks      # Tracks, search
├── .artists     # Artists, top tracks, discography, related artists
├── .albums      # Albums, new releases
├── .playlists   # Playlists, CRUD, track management
├── .player      # Playback control, queue, devices, history
├── .library     # Saved tracks/albums/shows/episodes, top items
├── .shows       # Podcast shows
├── .episodes    # Podcast episodes
└── .users       # Current user, public profiles, following
```

### Tracks — `sp.tracks`

| Method                                                                      | Description               |
| --------------------------------------------------------------------------- | ------------------------- |
| `search(query, *, limit, offset, market)`                                     | Search for tracks         |
| `get(track_id, *, market)`                                                  | Get a single track        |
| `get_many(track_ids, *, market)`                                            | Get multiple tracks       |

### Artists — `sp.artists`

| Method                                                        | Description          |
| ------------------------------------------------------------- | -------------------- |
| `search(query, *, limit, offset)`                               | Search for artists   |
| `get(artist_id)`                                              | Get a single artist  |
| `get_many(artist_ids)`                                        | Get multiple artists |
| `top_tracks(artist_id, *, market)`                            | Artist's top tracks  |
| `albums(artist_id, *, include_groups, market, limit, offset)` | Artist's discography |
| `related(artist_id)`                                          | Related artists      |

### Albums — `sp.albums`

| Method                                       | Description         |
| -------------------------------------------- | ------------------- |
| `search(query, *, limit, offset, market)`      | Search for albums   |
| `get(album_id, *, market)`                   | Get a single album  |
| `get_many(album_ids, *, market)`             | Get multiple albums |
| `tracks(album_id, *, limit, offset, market)` | Tracks in an album  |
| `new_releases(*, country, limit, offset)`    | New album releases  |

### Playlists — `sp.playlists`

| Method                                                                           | Description                                  |
| -------------------------------------------------------------------------------- | -------------------------------------------- |
| `search(query, *, limit, offset)`                                                  | Search for playlists                         |
| `get(playlist_id, *, market)`                                                    | Get a single playlist                        |
| `list(*, user_id, limit, offset)`                                                | Current user's (or another user's) playlists |
| `items(playlist_id, *, market, fields, limit, offset, additional_types)`        | Get playlist tracks and episodes                          |
| `create(name, *, public, collaborative, description, user_id)`                   | Create a playlist                            |
| `update(playlist_id, *, name, public, collaborative, description)`               | Update playlist details                      |
| `add(playlist_id, uris, *, position)`                                            | Add items to a playlist                      |
| `replace(playlist_id, uris)`                                                     | Replace all playlist items                   |
| `remove(playlist_id, uris)`                                                      | Remove items from a playlist                 |
| `reorder(playlist_id, *, range_start, insert_before, range_length, snapshot_id)` | Reorder items                                |
| `cover_image(playlist_id)`                                                       | Get playlist cover images                    |

### Player — `sp.player`

| Method                                                       | Description                                 |
| ------------------------------------------------------------ | ------------------------------------------- |
| `state(*, market)`                                           | Current playback state                      |
| `play(*, device_id, context_uri, uris, offset, position_ms)` | Start/resume playback                       |
| `pause(*, device_id)`                                        | Pause playback                              |
| `skip(*, device_id)`                                         | Skip to next track                          |
| `previous(*, device_id)`                                     | Skip to previous track                      |
| `seek(position_ms, *, device_id)`                            | Seek to position                            |
| `repeat(state, *, device_id)`                                | Set repeat mode (`track`, `context`, `off`) |
| `shuffle(state, *, device_id)`                               | Toggle shuffle                              |
| `volume(volume_percent, *, device_id)`                       | Set volume (0–100)                          |
| `queue()`                                                    | Get the player queue                        |
| `add_to_queue(uri, *, device_id)`                            | Add a track/episode to the queue            |
| `transfer(device_id, *, play)`                               | Transfer playback to another device         |
| `devices()`                                                  | List available devices                      |
| `recently_played(*, limit, after, before)`                   | Recently played tracks                      |

### Library — `sp.library`

| Method                                      | Description                 |
| ------------------------------------------- | --------------------------- |
| `saved_tracks(*, limit, offset, market)`    | User's saved tracks         |
| `saved_albums(*, limit, offset, market)`    | User's saved albums         |
| `saved_shows(*, limit, offset)`             | User's saved shows          |
| `saved_episodes(*, limit, offset)`          | User's saved episodes       |
| `save_tracks(track_ids)`                    | Save tracks                 |
| `remove_tracks(track_ids)`                  | Remove saved tracks         |
| `save_albums(album_ids)`                    | Save albums                 |
| `remove_albums(album_ids)`                  | Remove saved albums         |
| `save_shows(show_ids)`                      | Save shows                  |
| `remove_shows(show_ids)`                    | Remove saved shows          |
| `save_episodes(episode_ids)`                | Save episodes               |
| `remove_episodes(episode_ids)`              | Remove saved episodes       |
| `check_tracks(track_ids)`                   | Check if tracks are saved   |
| `check_albums(album_ids)`                   | Check if albums are saved   |
| `check_shows(show_ids)`                     | Check if shows are saved    |
| `check_episodes(episode_ids)`               | Check if episodes are saved |
| `top_tracks(*, time_range, limit, offset)`  | User's top tracks           |
| `top_artists(*, time_range, limit, offset)` | User's top artists          |

`time_range` accepts `"short_term"`, `"medium_term"`, or `"long_term"`.

### Shows — `sp.shows`

| Method                                        | Description         |
| --------------------------------------------- | ------------------- |
| `search(query, *, limit, offset, market)`       | Search for shows    |
| `get(show_id, *, market)`                     | Get a single show   |
| `get_many(show_ids, *, market)`               | Get multiple shows  |
| `episodes(show_id, *, market, limit, offset)` | Episodes for a show |

### Episodes — `sp.episodes`

| Method                                  | Description           |
| --------------------------------------- | --------------------- |
| `search(query, *, limit, offset, market)` | Search for episodes   |
| `get(episode_id, *, market)`            | Get a single episode  |
| `get_many(episode_ids, *, market)`      | Get multiple episodes |

### Users — `sp.users`

| Method                             | Description                            |
| ---------------------------------- | -------------------------------------- |
| `me()`                             | Current user's profile                 |
| `get(user_id)`                     | A public user's profile                |
| `following(*, type, limit, after)` | Artists the current user follows |
| `follow(type, ids)`                | Follow artists or users                |
| `unfollow(type, ids)`              | Unfollow artists or users              |
| `check_following(type, ids)`       | Check if following artists or users    |

## Retries

Spotify API requests automatically retry rate limits (`429`) and temporary server
errors (`500`, `502`, `503`, `504`). Rate limits honor Spotify's `Retry-After`
header. Server errors are retried only when the operation is safe to repeat. Configure the defaults with `max_retries` and
`retry_backoff_seconds` when constructing `SpotifyClient`.

The default client adds jitter to exponential backoff, caps that backoff at 30
seconds and stops automatic retries when a planned wait exceeds 60 seconds.
Rate limits cool concurrent requests on the same client. `QUOTA_EXCEEDED`
responses and ambiguous playlist reorders are not retried. Supply a `RetryPolicy`
to customize the retry count, backoff, jitter and maximum wait.

Use a request-context retry hook when planned retries should be reported to a
caller before spotifyify sleeps and sends the request again. The hook is
isolated per async task, so one shared `SpotifyClient` instance can be used by
concurrent conversations. `retry_number` is one-based and `retry_at` contains
the planned retry time in UTC:

```python
from spotifyify import RetryEvent

async def on_retry(event: RetryEvent) -> None:
    await sse_bus.emit(
        conversation_id,
        {
            "status_code": event.status_code,
            "retry_number": event.retry_number,
            "max_retries": event.max_retries,
            "retry_after": event.retry_after,
            "retry_at": event.retry_at.isoformat(),
        },
    )

async with spotify.request_context(on_retry=on_retry):
    track = await spotify.tracks.get(track_id)
```

If all retries are exhausted and Spotify still returns `429`, spotifyify raises
`SpotifyRateLimitError`. It subclasses `SpotifyAPIError` and exposes
`retry_after` and `retry_at` from Spotify's final `Retry-After` response header:

```python
from spotifyify import SpotifyRateLimitError

try:
    track = await spotify.tracks.get(track_id)
except SpotifyRateLimitError as exc:
    await sse_bus.emit(
        conversation_id,
        {
            "status_code": exc.status_code,
            "retry_after": exc.retry_after,
            "retry_at": exc.retry_at.isoformat() if exc.retry_at else None,
            "message": exc.message,
        },
    )
```

Request-scoped options can be combined without nested context managers:

```python
async with spotify.request_context(access_token=end_user_access_token, on_retry=on_retry):
    me = await spotify.users.me()
```

## Scopes

Use `SpotifyScope` to declare the OAuth scopes your app requires:

```python
from spotifyify import SpotifyScope

SpotifyScope.USER_READ_PLAYBACK_STATE
SpotifyScope.USER_MODIFY_PLAYBACK_STATE
SpotifyScope.USER_LIBRARY_READ
SpotifyScope.USER_LIBRARY_MODIFY
SpotifyScope.USER_TOP_READ
SpotifyScope.USER_READ_RECENTLY_PLAYED
SpotifyScope.PLAYLIST_MODIFY_PUBLIC
SpotifyScope.PLAYLIST_MODIFY_PRIVATE
SpotifyScope.PLAYLIST_READ_PRIVATE
```

Scopes can also be passed as plain strings.

## Examples

See the [`examples/`](./examples) directory for runnable Python scripts:

- [`examples/player/search_and_play.py`](./examples/player/search_and_play.py) — search for tracks and control playback with the Python API
- [`examples/playlists/manage_playlist.py`](./examples/playlists/manage_playlist.py) — create and manage a playlist with the Python API
- [`examples/playlists/user_token_playlist.py`](./examples/playlists/user_token_playlist.py) — create playlists with caller-supplied user tokens
- [`examples/library/library_stats.py`](./examples/library/library_stats.py) — explore your top tracks and saved library

## Development

```bash
uv sync --frozen --group schema --group examples
uv run --no-sync pytest -q
uv run --no-sync ruff check spotifyify tests examples tools
uv run --no-sync ruff format --check spotifyify tests examples tools
uv run --no-sync pyright
uv build
```

The CI tests Windows and Linux with Python 3.13 and 3.14, including the Python
client and MCP example. [Model maintenance](docs/models.md) documents the pinned schema and
comparison generator. [The migration guide](docs/migration-0.9.md) describes
compatibility changes in 0.9.
