# Read and discovery commands

Read this file only for search, lookup, profile, catalog, library-listing, playlist-listing, following-listing, or history requests.

## Contents

- [Shared notation](#shared-notation)
- [Catalog and profile](#catalog-and-profile)
- [Playlists](#playlists)
- [Library and history](#library-and-history)
- [Default output fields](#default-output-fields)

## Shared notation

- `QUERY`, `ID`, and `TYPE` are positional arguments.
- `ID...` means one or more positional IDs, separated by spaces or commas.
- `[--limit N]` accepts `1..50`.
- `[--field PATHS]` projects the returned JSON. It may be repeated and accepts comma-separated dotted paths.
- Put the root `--market CODE` before the group, not after the command.

## Catalog and profile

```text
spotifyify tracks search QUERY [--limit N] [--field PATHS]
spotifyify tracks get ID... [--field PATHS]

spotifyify artists search QUERY [--limit N] [--field PATHS]
spotifyify artists get ID... [--field PATHS]
spotifyify artists top-tracks ARTIST_ID [--field PATHS]
spotifyify artists albums ARTIST_ID [--include-groups GROUPS] [--limit N] [--field PATHS]
spotifyify artists related ARTIST_ID [--field PATHS]

spotifyify albums search QUERY [--limit N] [--field PATHS]
spotifyify albums get ID... [--field PATHS]
spotifyify albums tracks ALBUM_ID [--limit N] [--field PATHS]
spotifyify albums new-releases [--country CODE] [--limit N] [--field PATHS]

spotifyify shows search QUERY [--limit N] [--field PATHS]
spotifyify shows get ID... [--field PATHS]
spotifyify shows episodes SHOW_ID [--limit N] [--field PATHS]

spotifyify episodes search QUERY [--limit N] [--field PATHS]
spotifyify episodes get ID... [--field PATHS]

spotifyify users me [--field PATHS]
spotifyify users get USER_ID [--field PATHS]
spotifyify users following [--type artist] [--limit N] [--after CURSOR] [--field PATHS]
spotifyify users check-following TYPE ID... [--field PATHS]
```

For `artists albums`, `--include-groups` accepts a comma-separated subset of `album,single,appears_on,compilation`. Artist top tracks use the root market, falling back to `US`. `users following` currently defaults to and normally uses `artist`.

## Playlists

```text
spotifyify playlists search QUERY [--limit N] [--field PATHS]
spotifyify playlists get PLAYLIST_ID [--field PATHS]
spotifyify playlists list [--user-id USER_ID] [--limit N] [--field PATHS]
spotifyify playlists tracks PLAYLIST_ID [--spotify-fields EXPR] [--limit N] [--additional-type TYPE]... [--field PATHS]
spotifyify playlists cover-image PLAYLIST_ID [--field PATHS]
```

Use `playlists list` without `--user-id` for the current user's playlists. Use `playlists search` for global name discovery. On `playlists tracks`, `--additional-type` is repeatable; omit it for normal track items.

## Library and history

```text
spotifyify library saved-tracks [--limit N] [--field PATHS]
spotifyify library saved-albums [--limit N] [--field PATHS]
spotifyify library saved-shows [--limit N] [--field PATHS]
spotifyify library saved-episodes [--limit N] [--field PATHS]
spotifyify library top-tracks [--time-range RANGE] [--limit N] [--field PATHS]
spotifyify library top-artists [--time-range RANGE] [--limit N] [--field PATHS]

spotifyify library check-tracks ID... [--field PATHS]
spotifyify library check-albums ID... [--field PATHS]
spotifyify library check-shows ID... [--field PATHS]
spotifyify library check-episodes ID... [--field PATHS]

spotifyify player recently-played [--limit N] [--after UNIX_MS | --before UNIX_MS] [--field PATHS]
```

`--time-range` accepts `short_term`, `medium_term` (default), or `long_term`. Do not pass both `--after` and `--before` for recently played items.

## Default output fields

Use these paths when interpreting normal output or choosing a minimal `--field` projection:

| Command family | Default fields |
| --- | --- |
| track search/get | `id`, `name`, `artists`, `album.name`, `uri` |
| artist search/get/related | `id`, `name`, `uri` |
| artist top tracks | `id`, `name`, `artists`, `uri` |
| artist albums | `id`, `name`, `album_type`, `uri` |
| album search/get/new releases | `id`, `name`, `artists`, `uri` |
| album tracks | `id`, `name`, `artists`, `uri` |
| show search/get | `id`, `name`, `publisher`, `uri` |
| show episodes / episode search | `id`, `name`, `release_date`, `uri` |
| episode get | `id`, `name`, `show.name`, `uri` |
| playlist search/get/list | `id`, `name`, `owner`, `uri` |
| playlist tracks | `track.id`, `track.name`, `track.artists`, `added_at` |
| cover image | `url`, `width`, `height` |
| user me/get | `id`, `display_name`, `uri` |
| following artists | `id`, `name`, `uri` |
| following/library checks | `id`, `following` or `id`, `saved` |
| saved tracks | `track.id`, `track.name`, `track.artists`, `added_at` |
| saved albums | `album.id`, `album.name`, `album.artists`, `added_at` |
| saved shows | `show.id`, `show.name`, `show.publisher`, `added_at` |
| saved episodes | `episode.id`, `episode.name`, `added_at` |
| top tracks/artists | `id`, `name`, `artists` when applicable, `uri` |
| recently played | `track.id`, `track.name`, `track.artists`, `played_at` |
