# Persistent mutation commands

Read this file only when changing a library, following state, or playlist. These commands already return the resulting state; do not issue a follow-up read.

## Contents

- [Library](#library)
- [Following](#following)
- [Playlists](#playlists)
- [Mutation safeguards](#mutation-safeguards)

## Library

All `ID...` arguments accept space-separated or comma-separated IDs and batch internally.

```text
spotifyify library save-tracks ID... [--field PATHS]
spotifyify library remove-tracks ID... [--field PATHS]

spotifyify library save-albums ID... [--field PATHS]
spotifyify library remove-albums ID... [--field PATHS]

spotifyify library save-shows ID... [--field PATHS]
spotifyify library remove-shows ID... [--field PATHS]

spotifyify library save-episodes ID... [--field PATHS]
spotifyify library remove-episodes ID... [--field PATHS]
```

Success returns one row per requested ID with `id` and the resulting boolean `saved`.

## Following

`TYPE` is `artist` or `user`.

```text
spotifyify users follow TYPE ID... [--field PATHS]
spotifyify users unfollow TYPE ID... [--field PATHS]
```

Success returns one row per requested ID with `id` and the resulting boolean `following`.

## Playlists

```text
spotifyify playlists create NAME [--public | --private] [--collaborative | --not-collaborative] [--description TEXT] [--user-id USER_ID] [--field PATHS]

spotifyify playlists update PLAYLIST_ID [--name NAME] [--public | --private] [--collaborative | --not-collaborative] [--description TEXT] [--field PATHS]

spotifyify playlists add PLAYLIST_ID URI... [--position INDEX] [--field PATHS]
spotifyify playlists replace PLAYLIST_ID URI... [--field PATHS]
spotifyify playlists remove PLAYLIST_ID URI... [--field PATHS]

spotifyify playlists reorder PLAYLIST_ID --range-start INDEX --insert-before INDEX [--range-length N] [--snapshot-id ID] [--field PATHS]
```

Defaults and results:

- `create` defaults to private and not collaborative. It returns `id`, `name`, `owner`, and `uri`.
- `update` changes only supplied options. It returns `id`, `name`, `public`, `collaborative`, and `description`.
- `add`, `replace`, `remove`, and `reorder` return `playlist_id`, `snapshot_id`, and `total`.
- `URI...` accepts track or episode Spotify URIs as separate or comma-separated values.
- `--position`, `--range-start`, and `--insert-before` are zero-based.
- `--range-length` defaults to `1` and must be at least `1`.
- `--snapshot-id` provides optimistic concurrency protection when the caller already has a snapshot.

## Mutation safeguards

- Do not mutate a candidate selected solely because it is the first broad search hit. Resolve names to unambiguous IDs or URIs first.
- Preserve the user's item order for playlist `add` and `replace`.
- Use `replace` only for an explicit whole-playlist replacement. It removes all playlist entries not included in `URI...`.
- For `remove`, supply only the exact URIs requested.
- For `reorder`, confirm the zero-based source and destination indices from the current ordering when the request does not already provide them.
- Do not invent a playlist owner. Omit `--user-id` to create for the current user.
- A successful command's returned `saved`, `following`, `snapshot_id`, or updated playlist row is sufficient confirmation.
