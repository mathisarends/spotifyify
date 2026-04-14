"""Shared test fixtures: minimal-valid dicts for Spotify API response shapes."""

from __future__ import annotations


def paging(**overrides) -> dict:
    """Minimal valid PagingObject dict."""
    base = {
        "href": "https://api.spotify.com/v1/test",
        "items": [],
        "limit": 20,
        "next": "",
        "offset": 0,
        "previous": "",
        "total": 0,
    }
    base.update(overrides)
    return base


def cursor_paging(**overrides) -> dict:
    """Minimal valid CursorPagingObject dict."""
    base = {
        "href": "https://api.spotify.com/v1/test",
        "items": [],
        "limit": 20,
        "next": "",
        "cursors": None,
        "total": 0,
    }
    base.update(overrides)
    return base


def track(**overrides) -> dict:
    """Minimal valid TrackObject dict (only `type` is required)."""
    base = {"type": "track"}
    base.update(overrides)
    return base


def album(**overrides) -> dict:
    """Minimal valid AlbumObject dict."""
    base = {
        "album_type": "album",
        "total_tracks": 0,
        "available_markets": [],
        "external_urls": {},
        "href": "",
        "id": "album_id",
        "images": [],
        "name": "Test Album",
        "release_date": "2024-01-01",
        "release_date_precision": "day",
        "type": "album",
        "uri": "spotify:album:album_id",
        "artists": [],
        "tracks": paging(),
        "copyrights": [],
        "external_ids": {},
        "genres": [],
        "label": "Test Label",
        "popularity": 50,
    }
    base.update(overrides)
    return base


def artist(**overrides) -> dict:
    """Minimal valid ArtistObject dict."""
    base = {
        "external_urls": {},
        "href": "",
        "id": "artist_id",
        "name": "Test Artist",
        "type": "artist",
        "uri": "spotify:artist:artist_id",
    }
    base.update(overrides)
    return base


def episode(**overrides) -> dict:
    """Minimal valid EpisodeObject dict."""
    base = {
        "audio_preview_url": "",
        "description": "desc",
        "html_description": "<p>desc</p>",
        "duration_ms": 1000,
        "explicit": False,
        "external_urls": {},
        "href": "",
        "id": "ep_id",
        "images": [],
        "is_externally_hosted": False,
        "is_playable": True,
        "languages": ["en"],
        "name": "Test Episode",
        "release_date": "2024-01-01",
        "release_date_precision": "day",
        "type": "EpisodeObject",
        "uri": "spotify:episode:ep_id",
        "show": simplified_show(),
    }
    base.update(overrides)
    return base


def simplified_show(**overrides) -> dict:
    """Minimal valid SimplifiedShowObject dict."""
    base = {
        "available_markets": [],
        "copyrights": [],
        "description": "desc",
        "html_description": "<p>desc</p>",
        "explicit": False,
        "external_urls": {},
        "href": "",
        "id": "show_id",
        "images": [],
        "is_externally_hosted": False,
        "languages": ["en"],
        "media_type": "audio",
        "name": "Test Show",
        "publisher": "Publisher",
        "type": "show",
        "uri": "spotify:show:show_id",
        "total_episodes": 0,
    }
    base.update(overrides)
    return base


def show(**overrides) -> dict:
    """Minimal valid ShowObject dict (extends SimplifiedShow + episodes)."""
    base = simplified_show()
    base["episodes"] = paging()
    base.update(overrides)
    return base


def playlist(**overrides) -> dict:
    """Minimal valid PlaylistObject dict."""
    base = {
        "collaborative": False,
        "description": "",
        "external_urls": {},
        "href": "",
        "id": "playlist_id",
        "images": [],
        "name": "Test Playlist",
        "owner": {
            "external_urls": {},
            "href": "",
            "id": "owner_id",
            "type": "user",
            "uri": "",
        },
        "public": False,
        "snapshot_id": "snap",
        "tracks": paging(),
        "type": "playlist",
        "uri": "spotify:playlist:playlist_id",
    }
    base.update(overrides)
    return base
