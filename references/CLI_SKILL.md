---
name: use-spotifyify-cli
description: Operate Spotify through the spotifyify command-line interface for search, lookup, playback, queue, library, playlist, following, profile, and listening-history tasks. Use when a user asks in natural language to find, inspect, play, pause, queue, save, remove, follow, unfollow, create, update, or otherwise manage Spotify data with the `spotifyify` CLI. Translate the request to the shortest valid command, select only useful JSON fields, and avoid command-discovery or help calls.
---

# Use the spotifyify CLI

Translate the request directly into the shortest valid command. Do not use `--help`, probe commands, inspect source, or switch to the Python API.

## Operating rules

- Reuse supplied IDs and `spotify:...` URIs. Search only to resolve names; do not follow search with `get` for ordinary fields.
- Pass multiple IDs or URIs in one invocation, separated by spaces or commas. Supported commands batch internally.
- Before persistent changes, require unambiguous IDs or URIs. Ask when several plausible matches remain.
- Parse stdout as UTF-8 JSON. Mutations return their resulting state; do not issue confirmation reads.
- Report only the requested outcome.

## Shared syntax

```text
spotifyify [--market CODE] [--device-id ID] GROUP COMMAND ...
```

Global options precede the group and override `SPOTIFYIFY_MARKET` and `SPOTIFYIFY_DEVICE_ID`. Quote free text. Every command accepts `--field PATHS` (`--fields`, `-f`) with repeated or comma-separated dotted paths. Commands shown with `--limit N` accept `1..50`.

## Catalog

```text
spotifyify tracks search QUERY [--limit N]
spotifyify tracks get ID...

spotifyify artists search QUERY [--limit N]
spotifyify artists get ID...
spotifyify artists top-tracks ARTIST_ID
spotifyify artists albums ARTIST_ID [--include-groups GROUPS] [--limit N]
spotifyify artists related ARTIST_ID

spotifyify albums search QUERY [--limit N]
spotifyify albums get ID...
spotifyify albums tracks ALBUM_ID [--limit N]
spotifyify albums new-releases [--country CODE] [--limit N]

spotifyify shows search QUERY [--limit N]
spotifyify shows get ID...
spotifyify shows episodes SHOW_ID [--limit N]

spotifyify episodes search QUERY [--limit N]
spotifyify episodes get ID...
```

`artists albums --include-groups` accepts a comma-separated subset of `album,single,appears_on,compilation`.

## Playlists

```text
spotifyify playlists search QUERY [--limit N]
spotifyify playlists get PLAYLIST_ID
spotifyify playlists list [--user-id USER_ID] [--limit N]
spotifyify playlists tracks PLAYLIST_ID [--spotify-fields EXPR] [--limit N] [--additional-type TYPE]...
spotifyify playlists cover-image PLAYLIST_ID

spotifyify playlists create NAME [--public|--private] [--collaborative|--not-collaborative] [--description TEXT] [--user-id USER_ID]
spotifyify playlists update PLAYLIST_ID [--name NAME] [--public|--private] [--collaborative|--not-collaborative] [--description TEXT]
spotifyify playlists add PLAYLIST_ID URI... [--position INDEX]
spotifyify playlists replace PLAYLIST_ID URI...
spotifyify playlists remove PLAYLIST_ID URI...
spotifyify playlists reorder PLAYLIST_ID --range-start INDEX --insert-before INDEX [--range-length N] [--snapshot-id ID]
```

Use `list` for a user's playlists and `search` for global discovery. Creation defaults to private and non-collaborative. `--spotify-fields` filters Spotify's server response; `--field` projects CLI output. Playlist indices are zero-based and `--range-length` defaults to `1`. Preserve URI order. Use `replace` only for explicit whole-playlist replacement.

## Library and users

```text
spotifyify library saved-tracks [--limit N]
spotifyify library saved-albums [--limit N]
spotifyify library saved-shows [--limit N]
spotifyify library saved-episodes [--limit N]
spotifyify library top-tracks [--time-range RANGE] [--limit N]
spotifyify library top-artists [--time-range RANGE] [--limit N]

spotifyify library save-tracks ID...
spotifyify library remove-tracks ID...
spotifyify library check-tracks ID...
spotifyify library save-albums ID...
spotifyify library remove-albums ID...
spotifyify library check-albums ID...
spotifyify library save-shows ID...
spotifyify library remove-shows ID...
spotifyify library check-shows ID...
spotifyify library save-episodes ID...
spotifyify library remove-episodes ID...
spotifyify library check-episodes ID...

spotifyify users me
spotifyify users get USER_ID
spotifyify users following [--type artist] [--limit N] [--after CURSOR]
spotifyify users follow TYPE ID...
spotifyify users unfollow TYPE ID...
spotifyify users check-following TYPE ID...
```

`--time-range` accepts `short_term`, `medium_term` (default), or `long_term`. Follow `TYPE` is `artist` or `user`. Save/remove and follow/unfollow return the resulting `saved` or `following` value.

## Player

Use top-level `play` for named content; it resolves the top match and starts it in one call:

```text
spotifyify play WORDS... [--track NAME] [--artist NAME] [--album NAME] [--wait|--no-wait]
```

`--track` or bare words select one track; `--album` without either selects an album context; `--artist` alone selects an artist context. Combine filters to disambiguate. Bare words always select track mode.

```text
spotifyify player state
spotifyify player play [--context-uri URI] [--uri URI]... [--offset-json OBJECT] [--position-ms MS] [--wait|--no-wait]
spotifyify player pause [--wait|--no-wait]
spotifyify player skip [--wait|--no-wait]
spotifyify player previous [--wait|--no-wait]
spotifyify player seek POSITION_MS
spotifyify player repeat STATE
spotifyify player shuffle BOOLEAN
spotifyify player volume PERCENT
spotifyify player queue
spotifyify player add-to-queue URI...
spotifyify player devices
spotifyify player transfer DEVICE_ID [--play|--no-play] [--wait|--no-wait]
spotifyify player recently-played [--limit N] [--after UNIX_MS|--before UNIX_MS]
```

`player play` without a URI resumes. Use `--uri` for tracks/episodes and `--context-uri` for albums/artists/playlists. Keep default waiting for applied state. Offset is JSON such as `{"position":2}`. Positions are non-negative milliseconds; repeat is `track|context|off`, shuffle is `true|false`, volume is `0..100`. Transfer defaults to `--no-play`. Do not combine history `--after` and `--before`.

Playback defaults to `state,track,artists,device`; optional field paths include `album,progress_ms,duration_ms,shuffle,repeat,uri`.
