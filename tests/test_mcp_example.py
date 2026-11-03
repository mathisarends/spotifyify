"""Discover the example's tools over stdio without invoking Spotify operations."""

import asyncio
import sys
from pathlib import Path

import pytest

pytest.importorskip("mcp")

from mcp.client.session import ClientSession
from mcp.client.stdio import StdioServerParameters, stdio_client


@pytest.mark.asyncio
async def test_example_starts_and_exposes_tools_over_stdio():
    script = Path(__file__).resolve().parents[1] / "examples" / "mcp" / "mcp_server.py"
    parameters = StdioServerParameters(command=sys.executable, args=[str(script)])
    async with asyncio.timeout(30):
        async with stdio_client(parameters) as (reader, writer):
            async with ClientSession(reader, writer) as session:
                await session.initialize()
                result = await session.list_tools()
    assert {tool.name for tool in result.tools} == {
        "search_tracks",
        "playback_state",
        "play_track",
    }
