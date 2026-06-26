# spotifyify

An async-first Spotify client with a namespaced API and fully typed response models maintained in the codebase and aligned with the [official Spotify OpenAPI specification](https://developer.spotify.com/reference/web-api/open-api-schema.yaml).

## Requirements

- Python 3.13+
- A Spotify app registered at [developer.spotify.com](https://developer.spotify.com/dashboard)

## Installation

```bash
pip install spotifyify
```

With [uv](https://github.com/astral-sh/uv):

```bash
uv add spotifyify
```

Optional CLI:

```bash
uv add "spotifyify[cli]"
spotifyify --help
```

## Configuration

Credentials are loaded from environment variables (or a `.env` file via `pydantic-settings`):

| Variable                   | Required      | Description                           |
| -------------------------- | ------------- | ------------------------------------- |
| `SPOTIFY_CLIENT_ID`        | Yes           | Your app's client ID                  |
| `SPOTIFY_CLIENT_SECRET`    | Yes           | Your app's client secret              |
| `SPOTIFY_REDIRECT_URI`     | For user auth | OAuth redirect URI                    |
| `SPOTIFY_ACCESS_TOKEN`     | Optional      | Pre-existing access token             |
| `SPOTIFY_REFRESH_TOKEN`    | Optional      | Refresh token for automatic renewal   |
| `SPOTIFY_TOKEN_EXPIRES_AT` | Optional      | Unix timestamp when the token expires |

**.env example:**

```env
SPOTIFY_CLIENT_ID=your_client_id
SPOTIFY_CLIENT_SECRET=your_client_secret
SPOTIFY_REDIRECT_URI=http://localhost:8888/callback
SPOTIFY_REFRESH_TOKEN=your_refresh_token
```

If `SPOTIFY_REFRESH_TOKEN` (or `SPOTIFY_ACCESS_TOKEN`) is present the client operates in user mode. Without them it falls back to the [Client Credentials flow](https://developer.spotify.com/documentation/web-api/tutorials/client-credentials-flow), which only allows access to public data.

If a user-scoped endpoint is called and no user token is available, spotifyify starts an interactive Authorization Code login:

1. Opens the Spotify consent page in your browser.
2. Waits for the redirect on your configured `SPOTIFY_REDIRECT_URI` (for example `http://localhost:8888/callback`).
3. Exchanges the code for access and refresh tokens.
4. Stores tokens in `.spotify_cache` by default (already git-ignored in this project).

### Bring your own user token

Multi-user backends can pass an already minted end-user access token for one request scope. While the context is active, spotifyify sends that token directly and skips its configured OAuth provider, app credentials, cache, refresh, and scope checks. Expired or insufficient tokens surface as Spotify API errors.

The token context is isolated per async task, so one shared `Spotifyify` instance can serve concurrent users:

```python
async with Spotifyify() as spotify:
    async with spotify.session(access_token=end_user_access_token):
        playlist = await spotify.playlists.create("Weekly Mix", public=False)
        await spotify.playlists.replace(
            playlist.id,
            ["spotify:track:...", "spotify:track:..."],
        )
```

## Quick start

```python
import asyncio
from spotifyify import Spotifyify, SpotifyScope

async def main():
    async with Spotifyify(scopes=[SpotifyScope.USER_READ_PLAYBACK_STATE]) as sp:
        state = await sp.player.state()
        if state and state.item:
            print(f"Now playing: {state.item.name}")

asyncio.run(main())
```

## CLI

Install the optional Typer-based CLI with:

```bash
uv add "spotifyify[cli]"
```

Then call it as `spotifyify`. The CLI mirrors the public namespace API from
`spotifyify.namespaces` and uses the same environment variables and `.env`
loading as the Python client.

```bash
spotifyify tracks search "Daft Punk" --limit 5
spotifyify albums get 4aawyAB9vmqN3uQ7FjRGTy --json
spotifyify playlists list --scope playlist-read-private
```

Commands print compact tables by default. Use `--json` to print the raw
Pydantic response payload as JSON. Use `--field` / `--fields` to keep only the
field paths an agent or script needs; the option can be repeated or passed as a
comma-separated list.

```bash
spotifyify tracks search "Daft Punk" --limit 3 --field id --field name --field uri
spotifyify tracks search "Daft Punk" --json --fields items.0.id,items.0.name
spotifyify player state --json --fields item.name,is_playing,progress_ms
spotifyify library saved-tracks --json --fields track.id,track.name,added_at
```

IDs, URIs, scopes, and fields accept repeated values or comma-separated values:

```bash
spotifyify tracks get-many 4uLU6hMCjMI75M1A2tKUQC,0TnOYISbd1XYRBk9myaseg
spotifyify playlists add PLAYLIST_ID spotify:track:ID_1 spotify:track:ID_2
spotifyify playlists list --scope playlist-read-private,user-library-read
```

Common options are shared across namespaces where the underlying Spotify API
supports them:

| Option | Description |
| ------ | ----------- |
| `--json` | Print the raw Pydantic response payload as JSON instead of a compact table |
| `--field`, `--fields`, `-f` | Include only selected field paths; repeat it or pass comma-separated paths |
| `--scope`, `-s` | Request OAuth scopes; repeat it or pass comma-separated scopes |
| `--limit`, `-l` | Number of items to fetch, capped at Spotify's per-endpoint limits |
| `--offset`, `-o` | Result offset for paginated endpoints |
| `--market`, `-m` | ISO 3166-1 alpha-2 market code |
| `--device-id` | Target Spotify Connect device for playback commands |

Most user-scoped commands set the matching default scope automatically. Override
or extend scopes with `--scope` when you need a different authorization grant.
When a command needs user authorization and no token is configured yet, the CLI
uses the same interactive Authorization Code login and token cache as the Python
client.

Search and read commands render the most useful columns by default. Mutating
commands print `OK` or a Spotify snapshot ID by default. Add `--json` where
available for machine-readable output, for example:

```bash
spotifyify playlists add PLAYLIST_ID spotify:track:TRACK_ID --json
spotifyify library check-tracks TRACK_ID_1,TRACK_ID_2 --json
spotifyify users check-following artist ARTIST_ID --json
```

### CLI Commands

| Namespace | Commands |
| --------- | -------- |
| `tracks` | `search`, `get`, `get-many`, `audio-features`, `recommendations` |
| `artists` | `search`, `get`, `get-many`, `top-tracks`, `albums`, `related` |
| `albums` | `search`, `get`, `get-many`, `tracks`, `new-releases` |
| `playlists` | `search`, `get`, `list`, `tracks`, `create`, `update`, `add`, `replace`, `remove`, `reorder`, `cover-image` |
| `shows` | `search`, `get`, `get-many`, `episodes` |
| `episodes` | `search`, `get`, `get-many` |
| `library` | `saved-tracks`, `saved-albums`, `saved-shows`, `saved-episodes`, `top-tracks`, `top-artists`, `save-*`, `remove-*`, `check-*` for tracks/albums/shows/episodes |
| `player` | `state`, `play`, `pause`, `skip`, `previous`, `seek`, `repeat`, `shuffle`, `volume`, `queue`, `add-to-queue`, `transfer`, `devices`, `recently-played` |
| `users` | `me`, `get`, `following`, `follow`, `unfollow`, `check-following` |

Use Typer's built-in help to inspect exact arguments and options:

```bash
spotifyify --help
spotifyify playlists create --help
spotifyify player play --help
```

## API design

The `Spotifyify` class is the entry point. It exposes all Spotify resources as lazy-loaded namespace properties. Every method is a coroutine and must be awaited.

```
Spotifyify
├── .tracks      # Tracks, search, audio features, recommendations
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
| `find(query, *, limit, offset, market)`                                     | Search for tracks         |
| `get(track_id, *, market)`                                                  | Get a single track        |
| `get_many(track_ids, *, market)`                                            | Get up to 50 tracks       |
| `audio_features(track_ids)`                                                 | Audio features for tracks |
| `recommendations(*, seed_artists, seed_tracks, seed_genres, limit, market)` | Get recommendations       |

### Artists — `sp.artists`

| Method                                                        | Description          |
| ------------------------------------------------------------- | -------------------- |
| `find(query, *, limit, offset)`                               | Search for artists   |
| `get(artist_id)`                                              | Get a single artist  |
| `get_many(artist_ids)`                                        | Get up to 50 artists |
| `top_tracks(artist_id, *, market)`                            | Artist's top tracks  |
| `albums(artist_id, *, include_groups, market, limit, offset)` | Artist's discography |
| `related(artist_id)`                                          | Related artists      |

### Albums — `sp.albums`

| Method                                       | Description         |
| -------------------------------------------- | ------------------- |
| `find(query, *, limit, offset, market)`      | Search for albums   |
| `get(album_id, *, market)`                   | Get a single album  |
| `get_many(album_ids, *, market)`             | Get up to 20 albums |
| `tracks(album_id, *, limit, offset, market)` | Tracks in an album  |
| `new_releases(*, country, limit, offset)`    | New album releases  |

### Playlists — `sp.playlists`

| Method                                                                           | Description                                  |
| -------------------------------------------------------------------------------- | -------------------------------------------- |
| `find(query, *, limit, offset)`                                                  | Search for playlists                         |
| `get(playlist_id, *, market)`                                                    | Get a single playlist                        |
| `list(*, user_id, limit, offset)`                                                | Current user's (or another user's) playlists |
| `tracks(playlist_id, *, market, fields, limit, offset, additional_types)`        | Get playlist tracks                          |
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
| `find(query, *, limit, offset, market)`       | Search for shows    |
| `get(show_id, *, market)`                     | Get a single show   |
| `get_many(show_ids, *, market)`               | Get multiple shows  |
| `episodes(show_id, *, market, limit, offset)` | Episodes for a show |

### Episodes — `sp.episodes`

| Method                                  | Description           |
| --------------------------------------- | --------------------- |
| `find(query, *, limit, offset, market)` | Search for episodes   |
| `get(episode_id, *, market)`            | Get a single episode  |
| `get_many(episode_ids, *, market)`      | Get multiple episodes |

### Users — `sp.users`

| Method                             | Description                            |
| ---------------------------------- | -------------------------------------- |
| `me()`                             | Current user's profile                 |
| `get(user_id)`                     | A public user's profile                |
| `following(*, type, limit, after)` | Artists/users the current user follows |
| `follow(type, ids)`                | Follow artists or users                |
| `unfollow(type, ids)`              | Unfollow artists or users              |
| `check_following(type, ids)`       | Check if following artists or users    |

## Retries

Spotify API requests automatically retry rate limits (`429`) and temporary server
errors (`500`, `502`, `503`, `504`). Rate limits honor Spotify's `Retry-After`
header. Server errors are only retried for idempotent HTTP methods to avoid
duplicating mutations. Configure the defaults with `max_retries` and
`retry_backoff_seconds` when constructing `Spotifyify`.

Use a request-context retry hook when planned retries should be reported to a
caller before spotifyify sleeps and sends the request again. The hook is
isolated per async task, so one shared `Spotifyify` instance can be used by
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

async with spotify.session(on_retry=on_retry):
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
async with spotify.session(access_token=end_user_access_token, on_retry=on_retry):
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

See the [`examples/`](./examples) directory for runnable scripts:

- [`examples/search_and_play.py`](./examples/search_and_play.py) — search for tracks and control playback
- [`examples/manage_playlist.py`](./examples/manage_playlist.py) — create and manage a playlist
- [`examples/playlists/user_token_playlist.py`](./examples/playlists/user_token_playlist.py) — create playlists with caller-supplied user tokens
- [`examples/library_stats.py`](./examples/library_stats.py) — explore your top tracks and saved library
