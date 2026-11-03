import json
from unittest.mock import AsyncMock

import httpx2
import pytest

from spotifyify import SpotifyBatchError, SpotifyClient, SpotifyResponseError
from tests.conftest import cursor_paging, paging


@pytest.mark.asyncio
async def test_playlist_batches_preserve_insert_order_and_report_partial_failure():
    requests = []

    def respond(request):
        payload = json.loads(request.content)
        requests.append(payload)
        if len(requests) == 2:
            return httpx2.Response(503, json={"error": {"message": "failed"}})
        return httpx2.Response(201, json={"snapshot_id": "after-first"})

    async with SpotifyClient(transport=httpx2.MockTransport(respond)) as spotify:
        async with spotify.session(access_token="external"):
            with pytest.raises(SpotifyBatchError) as error:
                await spotify.playlists.add(
                    "p", [f"spotify:track:t{index}" for index in range(205)], position=3
                )
    assert requests[0]["position"] == 3
    assert requests[1]["position"] == 103
    assert len(requests[0]["uris"]) == 100
    assert error.value.completed_items == 100
    assert error.value.total_items == 205
    assert error.value.snapshot_id == "after-first"


@pytest.mark.asyncio
async def test_offset_iterator_uses_next_offset_and_stops_lazily():
    offsets = []

    def respond(request):
        offset = int(request.url.params["offset"])
        offsets.append(offset)
        return httpx2.Response(
            200,
            json=paging(
                limit=2,
                offset=offset,
                total=3,
                next="https://api.spotify.com/v1/me/tracks?offset=2"
                if offset == 0
                else None,
                items=[
                    {"track": {"type": "track", "id": str(index)}}
                    for index in range(offset, min(offset + 2, 3))
                ],
            ),
        )

    async with SpotifyClient(transport=httpx2.MockTransport(respond)) as spotify:
        async with spotify.session(access_token="external"):
            assert [
                item.track.id
                async for item in spotify.library.iter_saved_tracks(limit=2)
            ] == ["0", "1", "2"]
            assert offsets == [0, 2]
            offsets.clear()
            iterator = spotify.library.iter_saved_tracks(limit=2)
            assert (await anext(iterator)).track.id == "0"
            await iterator.aclose()
            assert offsets == [0]


@pytest.mark.asyncio
async def test_cursor_iterator_reuses_cursor_and_rejects_a_loop():
    seen = []

    def respond(request):
        seen.append(request.url.params.get("after"))
        return httpx2.Response(
            200,
            json={
                "artists": cursor_paging(
                    next="https://api.spotify.com/v1/me/following?after=last", items=[]
                )
            },
        )

    async with SpotifyClient(transport=httpx2.MockTransport(respond)) as spotify:
        async with spotify.session(access_token="external"):
            with pytest.raises(SpotifyResponseError, match="advance"):
                _ = [item async for item in spotify.users.iter_following()]
    assert seen == [None, "last"]


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "operation",
    [
        lambda spotify: spotify.player.volume(101),
        lambda spotify: spotify.player.seek(-1),
        lambda spotify: spotify.player.repeat("forever"),
        lambda spotify: spotify.player.play(
            context_uri="spotify:album:a", uris=["spotify:track:t"]
        ),
        lambda spotify: spotify.player.recently_played(after=1, before=2),
        lambda spotify: spotify.playlists.add("p", ["invalid-uri"]),
        lambda spotify: spotify.playlists.create(
            "name", public=True, collaborative=True
        ),
        lambda spotify: spotify.tracks.get("https://wrong/path"),
        lambda spotify: spotify.library.saved_tracks(limit=0),
    ],
)
async def test_invalid_inputs_fail_before_authentication(operation):
    provider = AsyncMock()
    async with SpotifyClient(token_provider=provider) as spotify:
        with pytest.raises(ValueError):
            await operation(spotify)
    provider.get_access_token.assert_not_awaited()
