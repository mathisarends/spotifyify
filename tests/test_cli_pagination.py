import json
from unittest.mock import AsyncMock, patch

import httpx2
import pytest

pytest.importorskip("typer")

from typer.testing import CliRunner

from spotifyify import SpotifyClient
from spotifyify.cli import app
from tests.conftest import paging


def factory(transport):
    def client(**kwargs):
        provider = AsyncMock()
        provider.get_access_token.return_value = "external"
        return SpotifyClient(token_provider=provider, transport=transport, **kwargs)

    return client


def test_cli_collects_offset_pages_through_the_real_sdk():
    offsets = []

    def respond(request):
        offset = int(request.url.params.get("offset", "0"))
        offsets.append(offset)
        return httpx2.Response(
            200,
            json={
                "tracks": paging(
                    offset=offset,
                    limit=2,
                    total=5,
                    next="https://api.spotify.com/v1/search?offset=4"
                    if offset == 2
                    else None,
                    items=[
                        {"type": "track", "id": str(index)}
                        for index in range(offset, min(offset + 2, 5))
                    ],
                )
            },
        )

    with patch(
        "spotifyify.cli.core.SpotifyClient",
        side_effect=factory(httpx2.MockTransport(respond)),
    ):
        result = CliRunner().invoke(
            app, ["tracks", "search", "query", "--offset", "2", "--limit", "2", "--all"]
        )
    assert result.exit_code == 0, result.output
    assert [row["id"] for row in json.loads(result.stdout)] == ["2", "3", "4"]
    assert offsets == [2, 4]


def test_full_output_preserves_nulls_unknown_fields_and_paging():
    payload = {
        "tracks": paging(
            items=[{"type": "track", "id": "t", "new_field": "value", "name": None}]
        )
    }
    with patch(
        "spotifyify.cli.core.SpotifyClient",
        side_effect=factory(
            httpx2.MockTransport(lambda request: httpx2.Response(200, json=payload))
        ),
    ):
        result = CliRunner().invoke(app, ["--full", "tracks", "search", "query"])
    assert result.exit_code == 0, result.output
    assert json.loads(result.stdout) == payload["tracks"]


@pytest.mark.parametrize("key", ["item", "track"])
def test_playlist_item_columns_handle_both_server_contracts(key):
    payload = paging(items=[{key: {"type": "track", "id": "t", "name": "Song"}}])
    with patch(
        "spotifyify.cli.core.SpotifyClient",
        side_effect=factory(
            httpx2.MockTransport(lambda request: httpx2.Response(200, json=payload))
        ),
    ):
        result = CliRunner().invoke(app, ["playlists", "items", "p"])
    assert result.exit_code == 0, result.output
    assert json.loads(result.stdout)[0]["item.name"] == "Song"
