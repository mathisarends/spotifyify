"""Standalone stdio MCP server. Run with: uv run --group examples python examples/mcp/mcp_server.py"""

import os
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from dataclasses import dataclass
from typing import Any

from mcp.server import MCPServer
from mcp.server.mcpserver import Context

from spotifyify import SpotifyClient, SpotifyScope


@dataclass
class AppContext:
    spotify: SpotifyClient


@asynccontextmanager
async def lifespan(server: MCPServer) -> AsyncIterator[AppContext]:
    async with SpotifyClient(
        scopes=[
            SpotifyScope.USER_READ_PLAYBACK_STATE,
            SpotifyScope.USER_MODIFY_PLAYBACK_STATE,
        ],
        api_mode=os.environ.get("SPOTIFYIFY_API_MODE", "development"),
        cache_profile=os.environ.get("SPOTIFYIFY_PROFILE", "default"),
    ) as spotify:
        yield AppContext(spotify)


mcp = MCPServer("Spotifyify example", lifespan=lifespan)


@mcp.tool()
async def search_tracks(
    query: str, ctx: Context[AppContext], limit: int = 10
) -> list[dict[str, Any]]:
    """Search Spotify tracks by name, artist or album."""
    page = await ctx.request_context.lifespan_context.spotify.tracks.search(
        query, limit=limit, market=os.environ.get("SPOTIFYIFY_MARKET", "DE")
    )
    return [
        {"id": item.id, "name": item.name, "uri": item.uri} for item in page.items or []
    ]


@mcp.tool()
async def playback_state(ctx: Context[AppContext]) -> dict[str, Any] | None:
    """Read current playback and the active device."""
    state = await ctx.request_context.lifespan_context.spotify.player.state()
    return state.model_dump(mode="json", exclude_unset=True) if state else None


@mcp.tool()
async def play_track(
    uri: str, ctx: Context[AppContext], device_id: str | None = None
) -> dict[str, bool]:
    """Request playback of one Spotify track URI on an available device."""
    await ctx.request_context.lifespan_context.spotify.player.play(
        uris=[uri], device_id=device_id
    )
    return {"accepted": True}


if __name__ == "__main__":
    mcp.run(transport="stdio")
