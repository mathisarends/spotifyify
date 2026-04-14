# Fix Plan: Failing Examples

## Summary

| Example | Status | Error |
|---|---|---|
| `albums/browse_album` | ✅ OK | — |
| `library/library_stats` | ✅ OK | — |
| `library/library_overview` | ✅ OK | — |
| `player/search_and_play` | ✅ OK | — |
| `tracks/search_tracks` | ✅ OK (DeprecationWarnings) | — |
| `shows/browse_show` | ✅ OK (DeprecationWarnings) | — |
| `episodes/search_episodes` | ✅ OK | — |
| `users/profile` | ✅ OK (DeprecationWarnings) | — |
| `playlists/list_playlists` | ❌ FAIL | `AttributeError: 'Spotifyify' object has no attribute 'http'` |
| `playlists/manage_playlist` | ❌ FAIL | `SpotifyAPIError: 404` on `/recommendations` |
| `artists/explore_artist` | ❌ FAIL | `ValidationError: Track.album.available_markets Field required` |
| `player/playback_status` | ❌ FAIL | `AttributeError: 'Queue' object has no attribute 'name'` |

---

## Bug 1 — `playlists/list_playlists`: `AttributeError: 'Spotifyify' object has no attribute 'http'`

**File:** `spotifyify/namespaces/playlists.py:15`

**Root cause:**
`Playlists.__init__` receives the full `Spotifyify` instance (unlike all other namespaces that receive `self._http` directly) and then tries to access `client.http`. But `Spotifyify` only exposes `_http` (private attribute) — there is no public `http` property.

**Fix:**
Add a public `http` property to `Spotifyify`:

```python
# spotifyify/spotifyify.py
@property
def http(self) -> SpotifyClient:
    return self._http
```

---

## Bug 2 — `playlists/manage_playlist`: `SpotifyAPIError: 404` on `tracks.recommendations()`

**File:** `examples/playlists/manage_playlist.py:10`

**Root cause:**
The example calls `sp.tracks.recommendations(...)` which hits the Spotify `/recommendations` endpoint. Spotify **removed this endpoint** for new apps as of November 27, 2024 (quota extension required). It now returns a `404` for apps without legacy access.

**Fix:**
Replace the `recommendations()` call in the example with an alternative that still works, for example fetching related artists' top tracks, or simply remove that section of the example and replace it with a `sp.playlists.create()` + `sp.playlists.add()` demo instead — which is more relevant to a playlist example anyway.

---

## Bug 3 — `artists/explore_artist`: `ValidationError: Track.album.available_markets Field required`

**File:** `spotifyify/schemas.py:1251`

**Root cause:**
`AlbumBase.available_markets` is declared as a required field (`...`):

```python
available_markets: list[str] = Field(
    ...,   # <-- required
    deprecated=True,
    ...
)
```

The Spotify API does **not** include `available_markets` in album objects returned by the `GET /artists/{id}/top-tracks` endpoint. Since the field is deprecated, Spotify omits it from many responses. Pydantic rejects the payload because the required field is missing.

**Fix:**
Make `available_markets` optional in `AlbumBase` (and analogously in `ShowBase` and `AudiobookBase` which have the same pattern):

```python
# spotifyify/schemas.py
available_markets: list[str] | None = Field(
    None,   # <-- optional, defaults to None
    deprecated=True,
    ...
)
```

---

## Bug 4 — `player/playback_status`: `AttributeError: 'Queue' object has no attribute 'name'`

**File:** `examples/player/playback_status.py:35`

**Root cause:**
`PlayerQueue.queue` is typed as `list[Queue]` where `Queue` is a `RootModel[Track | Episode]`. Accessing `.name` on a `RootModel` fails because the actual `Track`/`Episode` object lives at `.root`. The example does `t.name` but should use `t.root.name`.

```python
# schemas.py
class Queue(RootModel[Track | Episode]):
    root: Track | Episode = Field(..., discriminator="type")

class PlayerQueue(BaseModel):
    queue: list[Queue] | None = ...
```

**Fix (option A — fix the example):**
```python
# examples/player/playback_status.py:35
print(f"  {t.root.name}")
```

**Fix (option B — cleaner, fix the schema):**
Change `PlayerQueue.queue` to unwrap the `RootModel` so callers get `Track | Episode` directly:

```python
# spotifyify/schemas.py
class PlayerQueue(BaseModel):
    currently_playing: Track | Episode | None = Field(None, discriminator="type")
    queue: list[Track | Episode] | None = Field(None)
```

Option B is preferable since it removes the awkward `.root` indirection for all callers.
