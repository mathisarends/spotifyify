# spotifyify

Async Spotify Web API client with Pydantic models, built for integration with MCP agents.

## Installation

```bash
# Core library only
pip install spotifyify

# With MCP server
pip install spotifyify[mcp]

# With OpenAI Agents SDK (for testing mcp capabilities)
pip install spotifyify[mcp,agents]
```

## Setup

Create a `.env` file:

```env
SPOTIFY_CLIENT_ID=your_client_id
SPOTIFY_CLIENT_SECRET=your_client_secret
SPOTIFY_REDIRECT_URI=http://127.0.0.1:8080

# Required for agents extra
OPENAI_API_KEY=your_openai_api_key
```

Get your Spotify credentials at [developer.spotify.com/dashboard](https://developer.spotify.com/dashboard).

## Usage

### As a Python library

```python
import asyncio
from spotifyify import Spotifyify
from spotifyify.credentials import SpotifyCredentials
from spotifyify.views import SpotifyScope

async def main():
    client = Spotifyify(
        credentials=SpotifyCredentials(),
        scopes=[
            SpotifyScope.USER_READ_PLAYBACK_STATE,
            SpotifyScope.USER_MODIFY_PLAYBACK_STATE,
        ],
    )

    playback = await client.current_playback()
    if playback and playback.item:
        print(f"Now playing: {playback.item.name}")

    results = await client.search(q="Fred again", type="track", limit=5)
    for track in results.tracks.items:
        print(f"{track.name} — {', '.join(a.name for a in track.artists)}")

asyncio.run(main())
```

### As an MCP server

Run the server directly:

```bash
uv run spotify-mcp
```

Or connect it to an agent:

```python
import asyncio
from agents import Agent, Runner
from agents.mcp import MCPServerStdio
from dotenv import load_dotenv

load_dotenv(override=True)

async def main():
    async with MCPServerStdio(
        name="Spotify Server",
        params={"command": "uv", "args": ["run", "spotify-mcp"]},
    ) as spotify_server:
        agent = Agent(
            name="Spotify DJ",
            instructions="Du bist ein professioneller DJ Assistant.",
            mcp_servers=[spotify_server],
        )

        history = []
        while True:
            user_input = input("Du: ").strip()
            if user_input.lower() in ["exit", "quit"]:
                break

            history.append({"role": "user", "content": user_input})
            result = await Runner.run(agent, history)
            history = result.to_input_list()
            print(f"Assistant: {result.final_output}\n")

asyncio.run(main())
```

## MCP Tools

### Playback

| Tool                    | Description                                  |
| ----------------------- | -------------------------------------------- |
| `get_current_playback`  | Current playback state and track info        |
| `get_currently_playing` | Lightweight currently playing track          |
| `start_playback`        | Start playback via context URI or track URIs |
| `pause_playback`        | Pause current playback                       |
| `next_track`            | Skip to next track                           |
| `previous_track`        | Skip to previous track                       |
| `set_shuffle`           | Enable/disable shuffle                       |
| `set_repeat`            | Set repeat mode (`track`, `context`, `off`)  |
| `seek_track`            | Seek to position in current track            |
| `set_volume`            | Set device volume (0–100)                    |

### Devices

| Tool                | Description                              |
| ------------------- | ---------------------------------------- |
| `get_devices`       | List available devices and refresh cache |
| `transfer_playback` | Transfer playback to another device      |

### Queue

| Tool           | Description                |
| -------------- | -------------------------- |
| `get_queue`    | Get current playback queue |
| `add_to_queue` | Add track to queue         |

### Search

| Tool            | Description               |
| --------------- | ------------------------- |
| `search_tracks` | Search for tracks         |
| `search_albums` | Search for albums         |
| `search_shows`  | Search for podcasts/shows |

### Library

| Tool                  | Description                |
| --------------------- | -------------------------- |
| `get_saved_tracks`    | Get liked songs            |
| `save_tracks`         | Like tracks                |
| `remove_saved_tracks` | Unlike tracks              |
| `is_track_saved`      | Check if track is liked    |
| `get_saved_albums`    | Get saved albums           |
| `save_albums`         | Save albums to library     |
| `remove_saved_albums` | Remove albums from library |
| `is_album_saved`      | Check if album is saved    |
| `get_saved_shows`     | Get saved podcasts         |

### Playlists

| Tool                          | Description                  |
| ----------------------------- | ---------------------------- |
| `get_user_playlists`          | List user playlists          |
| `create_playlist`             | Create a new playlist        |
| `add_tracks_to_playlist`      | Add tracks to playlist       |
| `remove_tracks_from_playlist` | Remove tracks from playlist  |
| `play_playlist`               | Play a playlist              |
| `delete_playlist`             | Delete (unfollow) a playlist |

### Artists & Albums

| Tool                    | Description                |
| ----------------------- | -------------------------- |
| `get_artist`            | Get artist details         |
| `get_artist_top_tracks` | Get artist's top 10 tracks |
| `get_album`             | Get album details          |
| `album_tracks`          | Get all tracks of an album |
| `play_album`            | Play an album              |

### Discovery

| Tool                  | Description                                                  |
| --------------------- | ------------------------------------------------------------ |
| `get_recently_played` | Recently played tracks                                       |
| `get_top_tracks`      | User's top tracks (`short_term`, `medium_term`, `long_term`) |
| `get_top_artists`     | User's top artists                                           |
| `get_new_releases`    | New album releases                                           |
| `get_show_episodes`   | Episodes of a podcast                                        |
| `play_episode`        | Play a podcast episode                                       |

## Device Resolution

Devices are resolved by name at startup and cached automatically. Names are case-insensitive.

If a device isn't found, call `get_devices` to refresh the cache — e.g. after opening Spotify on a new device.

> **Note:** If Spotify is paused or inactive, call `transfer_playback` before `start_playback` to activate the device first.

## Architecture

```
spotifyify/
├── __init__.py          # Spotifyify, SpotifyScope
├── credentials.py       # Pydantic settings (reads from .env)
├── device_resolver.py   # Device name → ID cache
├── schemas.py           # Pydantic models for all API responses
├── views.py             # Shared response types
└── mcp/
    ├── server.py        # FastMCP server + tool definitions
    └── cli.py           # Entry point for spotify-mcp command
```

## Requirements

- Python 3.13+
- Spotify Premium (required for playback control)
