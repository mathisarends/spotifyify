# Examples

The namespace directories contain runnable Python examples for the async API.

Run a Python example from the repository root:

```bash
uv run python examples/tracks/search_tracks.py
uv run python examples/player/search_and_play.py
uv run python examples/playlists/manage_playlist.py
```

Before examples that access playback, private playlists or the user's library,
supply a user access/refresh token or follow the
[Python authorization example](../README.md#user-authorization). Request the scopes
needed by the example, such as `user-read-playback-state`,
`user-modify-playback-state`, `user-library-read`, `playlist-read-private`,
`playlist-modify-private`, `user-top-read`, `user-read-recently-played` or
`user-follow-read`.

The examples never prompt during API calls. Use an explicit loopback redirect URI
and see the API-mode notes in the root README. Catalog requests for shows and
episodes need a market when no user country is available.

| Area | Examples |
| --- | --- |
| Tracks | [`tracks/search_tracks.py`](./tracks/search_tracks.py) |
| Artists | [`artists/explore_artist.py`](./artists/explore_artist.py) |
| Albums | [`albums/browse_album.py`](./albums/browse_album.py) |
| Playlists | [`playlists/list_playlists.py`](./playlists/list_playlists.py), [`playlists/manage_playlist.py`](./playlists/manage_playlist.py), [`playlists/user_token_playlist.py`](./playlists/user_token_playlist.py) |
| Playback | [`player/playback_status.py`](./player/playback_status.py), [`player/search_and_play.py`](./player/search_and_play.py) |
| Library | [`library/library_overview.py`](./library/library_overview.py), [`library/library_stats.py`](./library/library_stats.py) |
| Shows and episodes | [`shows/browse_show.py`](./shows/browse_show.py), [`episodes/search_episodes.py`](./episodes/search_episodes.py) |
| Users | [`users/profile.py`](./users/profile.py) |
| Retries | [`retries.py`](./retries.py) |
| MCP | [`mcp/mcp_server.py`](./mcp/mcp_server.py) |

## MCP server

The standalone stdio example uses its declared optional dependency group:

```bash
uv run --group examples python examples/mcp/mcp_server.py
```

Configure that command in an MCP host with this repository as its working
directory. It exposes search and playback tools and shares one SpotifyClient for
the server lifespan. Playback requires the user authorization described above.
