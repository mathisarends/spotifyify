import gzip
import hashlib
import json
from pathlib import Path

import httpx
import pytest

from spotifyify import SpotifyClient
from spotifyify.cli.core import as_jsonable, rows
from spotifyify.models import (
    Album,
    Paging,
    Playlist,
    PlaylistItem,
    SimplifiedShow,
    Track,
    User,
)
from tests.conftest import album, paging, simplified_show


def test_removed_fields_unknown_fields_and_explicit_nulls():
    album_payload = {
        key: value
        for key, value in album().items()
        if key not in {"label", "popularity"}
    }
    show_payload = {
        key: value
        for key, value in simplified_show().items()
        if key not in {"publisher", "available_markets"}
    }
    assert Album.model_validate(album_payload).id == "album_id"
    assert SimplifiedShow.model_validate(show_payload).id == "show_id"
    payload = {
        "id": "user",
        "account_id": "stable",
        "display_name": None,
        "new_field": {"value": 1},
    }
    assert as_jsonable(User.model_validate(payload)) == payload
    assert (
        Paging[Track].model_validate(paging(items=[{"type": "track"}])).items[0].type
        == "track"
    )


@pytest.mark.parametrize(
    "collection_key,item_key", [("items", "item"), ("tracks", "track")]
)
def test_playlist_contracts_normalize_without_losing_compatibility(
    collection_key, item_key
):
    model = Playlist.model_validate(
        {
            collection_key: paging(
                items=[{item_key: {"type": "track", "id": "t", "name": "Song"}}]
            )
        }
    )
    assert model.items is model.tracks
    item = model.items.items[0]
    assert isinstance(item, PlaylistItem)
    assert item.item is item.track
    assert rows(model.items, ("item.id", "item.name")) == [
        {"item.id": "t", "item.name": "Song"}
    ]


@pytest.mark.asyncio
async def test_field_projection_does_not_require_omitted_metadata_or_discriminator():
    async with SpotifyClient(
        transport=httpx.MockTransport(
            lambda request: httpx.Response(
                200, json={"items": [{"item": {"uri": "spotify:track:t"}}]}
            )
        )
    ) as spotify:
        async with spotify.session(access_token="external"):
            page = await spotify.playlists.items("p", fields="items(item(uri))")
    assert page.total is None
    assert page.items[0].item["uri"] == "spotify:track:t"


def test_pinned_schema_checksum():
    root = Path(__file__).resolve().parents[1] / "schemas"
    metadata = json.loads((root / "source.json").read_text())
    assert (
        hashlib.sha256(
            gzip.decompress((root / "spotify.openapi.yaml.gz").read_bytes())
        ).hexdigest()
        == metadata["sha256"]
    )
