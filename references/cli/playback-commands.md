# Playback, device, and queue commands

Read this file only for playing named content, controlling playback, selecting a device, or inspecting/modifying the queue.

## Contents

- [Choose the route](#choose-the-route)
- [Resolve and play by name](#resolve-and-play-by-name)
- [Known URI and playback control](#known-uri-and-playback-control)
- [Devices, queue, and history](#devices-queue-and-history)
- [Playback result](#playback-result)

## Choose the route

- Named track, album, or artist: use top-level `spotifyify play`; it searches, chooses the top match, starts playback, and returns the new state in one call.
- Known track/episode URI, known context URI, or resume: use `spotifyify player play`.
- All other playback actions: use the matching `spotifyify player` command.
- Put `--device-id DEVICE_ID` before `play` or `player`. If omitted, Spotify's active device is used. A top-level or player `play` retries on a deterministic controllable device when Spotify reports no active device.

## Resolve and play by name

```text
spotifyify play WORDS... [--track NAME] [--artist NAME] [--album NAME] [--wait | --no-wait] [--field PATHS]
```

Selection rules:

- `--track` or any bare `WORDS...` resolves and plays one track.
- `--album` without a track or bare words resolves and plays the album context.
- `--artist` alone resolves and plays the artist context.
- Combine `--track`, `--artist`, and `--album` to narrow a track match.
- Do not add bare words when the intent is to play an album or artist context; bare words switch selection to a track.

Examples:

```text
spotifyify play --track "WHO'S THAT" --artist "Ikkimel"
spotifyify play --album "Discovery" --artist "Daft Punk"
spotifyify play --artist "Daft Punk"
spotifyify --device-id DEVICE_ID play "Around the World" --artist "Daft Punk"
```

No match exits with code `4`.

## Known URI and playback control

```text
spotifyify player state [--field PATHS]

spotifyify player play [--context-uri URI] [--uri URI]... [--offset-json JSON_OBJECT] [--position-ms MS] [--wait | --no-wait] [--field PATHS]
spotifyify player pause [--wait | --no-wait] [--field PATHS]
spotifyify player skip [--wait | --no-wait] [--field PATHS]
spotifyify player previous [--wait | --no-wait] [--field PATHS]

spotifyify player seek POSITION_MS [--field PATHS]
spotifyify player repeat STATE [--field PATHS]
spotifyify player shuffle BOOLEAN [--field PATHS]
spotifyify player volume PERCENT [--field PATHS]
```

Constraints:

- `player play` with no URI resumes current playback.
- Repeat `--uri` or use comma-separated values for a list. The first URI is used to confirm the applied state.
- `--context-uri` plays an album, artist, or playlist context.
- `--offset-json` must be one JSON object accepted by Spotify, for example `{"position":2}` or `{"uri":"spotify:track:..."}`. Use it only with a context.
- `POSITION_MS` and `--position-ms` are non-negative integers.
- `repeat STATE` accepts `track`, `context`, or `off`.
- `shuffle BOOLEAN` accepts Typer boolean values such as `true` or `false`.
- `volume PERCENT` accepts `0..100`.
- Keep `--wait` unless immediate response is explicitly preferred.

## Devices, queue, and history

```text
spotifyify player devices [--field PATHS]
spotifyify player transfer DEVICE_ID [--play | --no-play] [--wait | --no-wait] [--field PATHS]

spotifyify player queue [--field PATHS]
spotifyify player add-to-queue URI... [--field PATHS]

spotifyify player recently-played [--limit N] [--after UNIX_MS | --before UNIX_MS] [--field PATHS]
```

- `transfer` defaults to `--no-play`; pass `--play` to start playback on the destination.
- `add-to-queue` accepts track or episode URIs, preserves their order, and submits all of them in one CLI invocation.
- Do not pass both `--after` and `--before` to `recently-played`.

## Playback result

Playback state reads and mutations normally return:

```json
[
  {
    "state": "playing",
    "track": "Track name",
    "artists": ["Artist name"],
    "device": "Device name"
  }
]
```

The default projected fields are `state`, `track`, `artists`, and `device`. Additional available playback paths include `album`, `progress_ms`, `duration_ms`, `shuffle`, `repeat`, and `uri`; request them with `--field`.

`player queue` returns `id`, `name`, `artists`, and `uri`. `player devices` returns `id`, `name`, `type`, `is_active`, and `volume_percent`.
