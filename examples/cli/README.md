# CLI examples

These recipes use the current plural resource groups and canonical command
names. Run `spotifyify ...` after installing the CLI globally, or prefix every
command with `uv run` when working from this checkout:

```bash
uv sync --extra cli
uv run spotifyify --help
```

The same Spotify credentials described in the project
[README](../../README.md#configuration) apply here. Commands that require a
user scope open the interactive login flow when necessary.

## Discover commands

Help is available at the root, namespace, and individual command levels:

```bash
spotifyify -h
spotifyify playlists -h
spotifyify playlists create -h
```

## Search and fetch

Search results and fetched resources are JSON arrays with stable, declared
columns:

```bash
spotifyify tracks search "Daft Punk" --limit 3
spotifyify artists search "Radiohead" --limit 3
spotifyify albums get 4aawyAB9vmqN3uQ7FjRGTy
spotifyify shows search "Lex Fridman" --limit 3
```

`get` accepts multiple IDs, either as separate arguments or comma-separated:

```bash
spotifyify tracks get TRACK_ID_1 TRACK_ID_2 TRACK_ID_3
spotifyify albums get ALBUM_ID_1,ALBUM_ID_2
```

The CLI splits large ID lists into the request sizes supported by Spotify and
combines the results into one JSON array.

## Select output fields

Use `--field`/`-f` to replace a command's default columns. It can be repeated,
and comma-separated field paths are accepted. Nested fields use dot notation:

```bash
spotifyify tracks search "Daft Punk" -f id,name,uri
spotifyify tracks get TRACK_ID -f id -f name -f album.name
spotifyify playlists tracks PLAYLIST_ID -f track.id,track.name,added_at
```

`playlists tracks` additionally supports Spotify's server-side field filter:

```bash
spotifyify playlists tracks PLAYLIST_ID \
  --spotify-fields "items(track(id,name)),next,total"
```

`--spotify-fields` controls what Spotify sends. `--field` controls the final
columns printed by spotifyify.

## Markets and devices

`--market` and `--device-id` are root options, so place them before the resource
group:

```bash
spotifyify --market DE tracks search "Daft Punk"
spotifyify player devices
spotifyify --device-id DEVICE_ID player state
```

They can also be configured with `SPOTIFYIFY_MARKET` and
`SPOTIFYIFY_DEVICE_ID`. An explicit option takes precedence over the
environment.

## Find and play in one command

The top-level `play` command resolves the first matching result and starts it:

```bash
spotifyify play --artist Ikkimel --track "WHO'S THAT"
spotifyify play --artist "Daft Punk" --album "Random Access Memories"
spotifyify play --artist "Daft Punk"
spotifyify play Get Lucky
```

A track name or free text plays one track. With no track, an album filter plays
the album context; with only an artist, it plays the artist context. If no
active Spotify device exists, the command selects a controllable device and
retries.

Playback mutations return the resulting state:

```bash
spotifyify player play --uri spotify:track:TRACK_ID
spotifyify player pause
spotifyify player skip
spotifyify player seek 60000
spotifyify player volume 35
spotifyify player add-to-queue spotify:track:TRACK_ID_1 spotify:track:TRACK_ID_2
```

They briefly wait for Spotify to reflect the change. Add `--no-wait` to a
playback command when an immediate read is preferable:

```bash
spotifyify player skip --no-wait
```

## Manage a playlist

Create a private playlist, then use the returned `id` in subsequent commands:

```bash
spotifyify playlists create "My Boards of Canada Mix" \
  --private \
  --description "Created with spotifyify"

spotifyify playlists add PLAYLIST_ID \
  spotify:track:TRACK_ID_1 \
  spotify:track:TRACK_ID_2

spotifyify playlists tracks PLAYLIST_ID
spotifyify playlists remove PLAYLIST_ID spotify:track:TRACK_ID_1
```

Playlist mutations report the new snapshot and total item count:

```json
[
  {
    "playlist_id": "PLAYLIST_ID",
    "snapshot_id": "NEW_SNAPSHOT_ID",
    "total": 2
  }
]
```

## Library and following

Commands that take IDs support the same repeated and comma-separated forms:

```bash
spotifyify library save-tracks TRACK_ID_1,TRACK_ID_2
spotifyify library check-tracks TRACK_ID_1 TRACK_ID_2
spotifyify library remove-tracks TRACK_ID_1 TRACK_ID_2

spotifyify users follow artist ARTIST_ID_1 ARTIST_ID_2
spotifyify users check-following artist ARTIST_ID_1,ARTIST_ID_2
spotifyify users unfollow artist ARTIST_ID_1 ARTIST_ID_2
```

Write commands read the state back and return one row per requested ID, for
example:

```json
[
  {"id": "TRACK_ID_1", "saved": true},
  {"id": "TRACK_ID_2", "saved": true}
]
```

## Raw Spotify responses

The default output deliberately contains only useful, stable columns. Set
`SPOTIFYIFY_RAW=1` to inspect the untouched Spotify payload, including paging
metadata and undeclared fields.

Bash:

```bash
SPOTIFYIFY_RAW=1 spotifyify tracks search "Daft Punk" --limit 1
```

PowerShell:

```powershell
$env:SPOTIFYIFY_RAW = "1"
spotifyify tracks search "Daft Punk" --limit 1
Remove-Item Env:SPOTIFYIFY_RAW
```

Every successful normal command writes JSON to stdout, so its output can be
redirected or consumed by another program without changing shape:

```bash
spotifyify tracks search "Daft Punk" --limit 5 > tracks.json
```
