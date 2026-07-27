---
name: use-spotifyify-cli
description: Operate Spotify through the spotifyify command-line interface for search, lookup, playback, queue, library, playlist, following, profile, and listening-history tasks. Use when a user asks in natural language to find, inspect, play, pause, queue, save, remove, follow, unfollow, create, update, or otherwise manage Spotify data with the `spotifyify` CLI. Translate the request to the shortest valid command, select only useful JSON fields, and avoid command-discovery or help calls.
---

# Use the spotifyify CLI

Translate the user's intent directly into the shortest valid `spotifyify` invocation. Do not call `--help`, probe command spellings, inspect package source, or use the Python API when this skill contains the needed route.

## Execution loop

1. Classify the intent as read, playback, or persistent mutation.
2. Extract identifiers already supplied by the user. Accept Spotify IDs where an `ID` is required and full `spotify:...` URIs where a `URI` is required. Do not look up an item that is already identified.
3. Choose the command from the routing table below.
4. Read exactly one detailed reference only if its signature or options are needed:
   - Reads and discovery: [cli/read-commands.md](cli/read-commands.md)
   - Library, following, and playlist mutations: [cli/mutation-commands.md](cli/mutation-commands.md)
   - Playback, devices, and queue: [cli/playback-commands.md](cli/playback-commands.md)
5. Execute the command once. Parse stdout as JSON; treat stderr and the exit code as diagnostics.
6. Use returned state as confirmation. Mutation commands already read back the resulting state; do not add a confirmation command.
7. Report the outcome in the user's language. Include only details relevant to the request.

## Fast routing

| Natural-language intent | Shortest route |
| --- | --- |
| Find tracks, artists, albums, playlists, shows, or episodes | `spotifyify <resource> search QUERY` |
| Get known track, artist, album, show, or episode IDs | `spotifyify <resource> get ID...` |
| Get a known playlist or user | `spotifyify playlists get ID` / `spotifyify users get ID` |
| Who am I? | `spotifyify users me` |
| List my playlists | `spotifyify playlists list` |
| List another user's playlists | `spotifyify playlists list --user-id ID` |
| Play a named track, album, or artist | top-level `spotifyify play ...` |
| Play a known URI or resume playback | `spotifyify player play ...` |
| Inspect or control current playback | `spotifyify player <state|pause|skip|previous|seek|repeat|shuffle|volume>` |
| Inspect or add to the queue | `spotifyify player queue` / `spotifyify player add-to-queue URI...` |
| List devices or move playback | `spotifyify player devices` / `spotifyify player transfer DEVICE_ID` |
| View saved or top items | `spotifyify library <saved-*|top-*>` |
| Save, remove, or check library items | `spotifyify library <save-*|remove-*|check-*> ID...` |
| View, follow, unfollow, or check followed accounts | `spotifyify users <following|follow|unfollow|check-following>` |
| Inspect or modify a playlist | `spotifyify playlists <tracks|create|update|add|replace|remove|reorder>` |
| Recent listening history | `spotifyify player recently-played` |

Resource group names are always plural: `tracks`, `artists`, `albums`, `playlists`, `shows`, `episodes`, `library`, `player`, and `users`.

## High-value direct routes

Prefer these over multi-call workflows:

```text
# Resolve the top matching track and play it
spotifyify play --track "TRACK" --artist "ARTIST"

# Play an album or artist context
spotifyify play --album "ALBUM" --artist "ARTIST"
spotifyify play --artist "ARTIST"

# Fetch many known IDs; comma-separated and space-separated forms both work
spotifyify tracks get ID_1 ID_2 ID_3
spotifyify albums get ID_1,ID_2

# Return only what the task needs
spotifyify tracks search "QUERY" --limit 5 --field id,name,artists,uri

# Mutate many items in one CLI call
spotifyify library save-tracks ID_1 ID_2
spotifyify playlists add PLAYLIST_ID spotify:track:ID_1 spotify:track:ID_2
```

Do not run `search` followed by `get` merely to retrieve normal display fields; search results already contain useful fields. Do not loop over IDs or URIs; variadic commands batch internally.

## Invocation rules

- Put global options before the command group:

  ```text
  spotifyify --market DE tracks search "QUERY"
  spotifyify --device-id DEVICE_ID player pause
  ```

- `--market CODE` / `-m CODE` overrides `SPOTIFYIFY_MARKET`.
- `--device-id ID` overrides `SPOTIFYIFY_DEVICE_ID`.
- Quote free text containing spaces or shell metacharacters.
- Pass IDs and URIs as separate arguments or comma-separated values. Preserve their order.
- Use `--limit N` / `-l N` only when the request implies a count; the default is usually 10 or 20 and the maximum is 50.
- Use `--field PATHS` / `--fields PATHS` / `-f PATHS` to replace default output columns. Paths may be comma-separated, repeated, and dotted, such as `album.name`.
- Use `--spotify-fields EXPR` only on `playlists tracks` when the user needs Spotify's server-side playlist-field filter. It is not an output projection.
- Keep the default `--wait` for playback mutations so the JSON describes the applied state. Use `--no-wait` only when latency matters more than confirmation.

## Resolve ambiguity without wandering

- For read-only discovery, return a small candidate list rather than guessing an exact match.
- For `spotifyify play`, the user is explicitly asking to play the top match; include artist and album filters when supplied to reduce ambiguity.
- Before a persistent mutation, require an unambiguous ID or URI. If the user supplied only a name, run one narrow search with `--limit 5 --field id,name,artists,uri`, then use an exact match. If several plausible matches remain, ask the user to choose; do not mutate the top hit silently.
- Treat `playlists replace` as destructive because it replaces every playlist item. Use it only when replacement of the whole contents is explicit.
- Do not run a mutation just to test authentication or command syntax.

## Output and failures

Every command emits UTF-8 JSON to stdout and plain diagnostics to stderr. Normal output is an array of row objects, including single-object reads and mutation confirmations.

| Exit | Meaning | Response |
| ---: | --- | --- |
| `0` | Success | Use the JSON result. An empty array means no matching/current item, not a CLI failure. |
| `1` | Spotify API error | Report the stderr message; retry only when it identifies a transient condition. |
| `2` | Invalid invocation | Correct the command from the relevant reference; do not reach for `--help`. |
| `3` | Authentication/configuration error | Report the missing or rejected credential. Do not repeat unchanged. |
| `4` | Top-level `play` found no match | Refine the query once if the request provides more qualifiers; otherwise report no match. |

The CLI requests command-specific OAuth scopes automatically. Public reads can use client credentials; user library, following, playlist-private, and playback operations require user authorization. Never print credential values.

If the executable is missing and installation is in scope, install the optional CLI with `uv add "spotifyify[cli]"` for a project or `uv tool install "spotifyify[cli]"` globally. Do not install or change credentials merely to answer a read-only question about how to form a command.

Set `SPOTIFYIFY_RAW=1` only for debugging an undeclared Spotify payload field. Normal agent work should prefer stable projected JSON.
