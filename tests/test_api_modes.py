import asyncio
import json

import httpx
import pytest

from spotifyify import SpotifyClient, SpotifyUnsupportedOperation
from tests.conftest import paging


@pytest.mark.asyncio
async def test_development_routes_and_uri_batches():
    requests = []

    def respond(request):
        requests.append(request)
        if request.url.path.endswith("/contains"):
            return httpx.Response(
                200, json=[True] * len(request.url.params["uris"].split(","))
            )
        if request.method == "GET":
            return httpx.Response(200, json=paging())
        return (
            httpx.Response(200, json={"id": "playlist"})
            if request.method == "POST"
            else httpx.Response(204)
        )

    async with SpotifyClient(transport=httpx.MockTransport(respond)) as spotify:
        async with spotify.session(access_token="external"):
            created = await spotify.playlists.create("Mix")
            assert created.id == "playlist"
            await spotify.playlists.items("playlist")
            await spotify.library.save_tracks([f"t{i}" for i in range(85)])
            assert await spotify.library.check_tracks(["t0", "t1"]) == [True, True]
            await spotify.users.follow("artist", ["artist"])
            with pytest.raises(SpotifyUnsupportedOperation):
                await spotify.users.get("other")
            with pytest.raises(SpotifyUnsupportedOperation):
                await spotify.albums.new_releases()
    assert requests[0].url.path == "/v1/me/playlists"
    assert json.loads(requests[0].content)["name"] == "Mix"
    assert requests[1].url.path == "/v1/playlists/playlist/items"
    writes = [request for request in requests if request.method == "PUT"]
    assert [len(request.url.params["uris"].split(",")) for request in writes] == [
        40,
        40,
        5,
        1,
    ]
    assert writes[-1].url.params["uris"] == "spotify:artist:artist"


@pytest.mark.asyncio
async def test_development_bulk_reads_are_bounded_and_keep_missing_positions():
    active = maximum = 0

    async def respond(request):
        nonlocal active, maximum
        active += 1
        maximum = max(maximum, active)
        await asyncio.sleep(0)
        active -= 1
        item_id = request.url.path.rsplit("/", 1)[-1]
        return (
            httpx.Response(404, json={})
            if item_id == "missing"
            else httpx.Response(200, json={"type": "track", "id": item_id})
        )

    async with SpotifyClient(
        transport=httpx.MockTransport(respond), concurrency=2
    ) as spotify:
        async with spotify.session(access_token="external"):
            results = await spotify.tracks.get_many(["one", "missing", "two", "three"])
            assert await spotify.tracks.get_many([]) == []
    assert [item.id if item else None for item in results] == [
        "one",
        None,
        "two",
        "three",
    ]
    assert maximum == 2


@pytest.mark.asyncio
async def test_extended_mode_batches_at_the_endpoint_limit():
    sizes = []

    def respond(request):
        ids = request.url.params["ids"].split(",")
        sizes.append(len(ids))
        return httpx.Response(
            200,
            json={
                "tracks": [
                    {"type": "track", "id": item_id} if item_id != "missing" else None
                    for item_id in ids
                ]
            },
        )

    ids = [str(index) for index in range(104)] + ["missing"]
    async with SpotifyClient(
        api_mode="extended", transport=httpx.MockTransport(respond)
    ) as spotify:
        async with spotify.session(access_token="external"):
            result = await spotify.tracks.get_many(ids)
    assert sizes == [50, 50, 5]
    assert len(result) == 105 and result[-1] is None


@pytest.mark.asyncio
async def test_development_search_limit_and_accidental_single_string_fail_before_http():
    def unexpected(request):
        pytest.fail("Invalid input must not send a request")

    async with SpotifyClient(transport=httpx.MockTransport(unexpected)) as spotify:
        with pytest.raises(ValueError, match="1..10"):
            await spotify.tracks.search("query", limit=11)
        with pytest.raises(ValueError, match="collection"):
            await spotify.tracks.get_many("one")
