"""Spotify paging response models; see schemas/source.json and docs/models.md."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from pydantic import Field

from .base import SpotifyModel

if TYPE_CHECKING:
    from .albums import ArtistDiscographyAlbum as ArtistDiscographyAlbum
    from .albums import SavedAlbum as SavedAlbum
    from .albums import SimplifiedAlbum as SimplifiedAlbum
    from .artists import Artist as Artist
    from .audiobooks import SimplifiedAudiobook as SimplifiedAudiobook
    from .audiobooks import SimplifiedChapter as SimplifiedChapter
    from .episodes import SavedEpisode as SavedEpisode
    from .episodes import SimplifiedEpisode as SimplifiedEpisode
    from .playlists import PlaylistItem as PlaylistItem
    from .playlists import SimplifiedPlaylist as SimplifiedPlaylist
    from .shows import SavedShow as SavedShow
    from .shows import SimplifiedShow as SimplifiedShow
    from .tracks import PlayHistory as PlayHistory
    from .tracks import SavedTrack as SavedTrack
    from .tracks import SimplifiedTrack as SimplifiedTrack
    from .tracks import Track as Track


class Cursor(SpotifyModel):
    after: str | None = Field(
        None, description="The cursor to use as key to find the next page of items."
    )
    before: str | None = Field(
        None, description="The cursor to use as key to find the previous page of items."
    )


class CursorPaging[T = Any](SpotifyModel):
    href: str | None = Field(
        None,
        description="A link to the Web API endpoint returning the full result of the request.",
    )
    limit: int | None = Field(
        None,
        description="The maximum number of items in the response (as set in the query or by default).",
    )
    next: str | None = Field(
        None, description="URL to the next page of items. ( `null` if none)"
    )
    cursors: Cursor | None = Field(
        None, description="The cursors used to find the next set of items."
    )
    total: int | None = Field(
        None, description="The total number of items available to return."
    )
    items: list[T] | None = None


class Paging[T = Any](SpotifyModel):
    href: str = Field(
        ...,
        description="A link to the Web API endpoint returning the full result of the request\n",
        examples=["https://api.spotify.com/v1/me/shows?offset=0&limit=20\n"],
    )
    limit: int = Field(
        ...,
        description="The maximum number of items in the response (as set in the query or by default).\n",
        examples=[20],
    )
    next: str | None = Field(
        None,
        description="URL to the next page of items. ( `null` if none)\n",
        examples=["https://api.spotify.com/v1/me/shows?offset=1&limit=1"],
    )
    offset: int = Field(
        ...,
        description="The offset of the items returned (as set in the query or by default)\n",
        examples=[0],
    )
    previous: str | None = Field(
        None,
        description="URL to the previous page of items. ( `null` if none)\n",
        examples=["https://api.spotify.com/v1/me/shows?offset=1&limit=1"],
    )
    total: int = Field(
        ...,
        description="The total number of items available to return.\n",
        examples=[4],
    )
    items: list[T] | None = None


class CursorPagingSimplifiedArtist(CursorPaging["Artist"]):
    pass


class PagingSimplifiedTrack(Paging["SimplifiedTrack"]):
    pass


class PagingArtist(Paging["Artist"]):
    pass


class PagingArtistDiscographyAlbum(Paging["ArtistDiscographyAlbum"]):
    pass


class PagingSimplifiedAlbum(Paging["SimplifiedAlbum"]):
    pass


class PagingSimplifiedShow(Paging["SimplifiedShow"]):
    pass


class PagingSimplifiedAudiobook(Paging["SimplifiedAudiobook"]):
    pass


class CursorPagingPlayHistory(CursorPaging["PlayHistory"]):
    pass


class PagingPlaylist(Paging["SimplifiedPlaylist | None"]):
    pass


class PagingFeaturedPlaylist(SpotifyModel):
    message: str | None = Field(
        None,
        description="The localized message of a playlist.\n",
        examples=["Popular Playlists"],
    )
    playlists: PagingPlaylist | None = None


class PagingSavedAlbum(Paging["SavedAlbum"]):
    pass


class PagingTrack(Paging["Track"]):
    pass


class PagingPlaylistItem(Paging["PlaylistItem"]):
    pass


class PagingSavedShow(Paging["SavedShow"]):
    pass


class PagingSimplifiedEpisode(Paging["SimplifiedEpisode | None"]):
    pass


class PagingSimplifiedChapter(Paging["SimplifiedChapter"]):
    pass


class PagingSavedTrack(Paging["SavedTrack"]):
    pass


class PagingSavedEpisode(Paging["SavedEpisode"]):
    pass
