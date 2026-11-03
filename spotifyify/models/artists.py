"""Spotify artists response models; see schemas/source.json and docs/models.md."""

from __future__ import annotations

from typing import TYPE_CHECKING

from pydantic import Field

from .base import SpotifyModel

if TYPE_CHECKING:
    from .common import ArtistObjectType, ExternalUrl, Followers, Image


class Artist(SpotifyModel):
    external_urls: ExternalUrl | None = Field(
        None, description="Known external URLs for this artist.\n"
    )
    followers: Followers | None = Field(
        None,
        deprecated=True,
        description="Information about the followers of the artist.\n",
    )
    genres: list[str] | None = Field(
        None,
        deprecated=True,
        description="A list of the genres the artist is associated with. If not yet classified, the array is empty.\n",
        examples=[["Prog rock", "Grunge"]],
    )
    href: str | None = Field(
        None,
        description="A link to the Web API endpoint providing full details of the artist.\n",
    )
    id: str | None = Field(
        None,
        description="The [Spotify ID](/documentation/web-api/concepts/spotify-uris-ids) for the artist.\n",
    )
    images: list[Image] | None = Field(
        None, description="Images of the artist in various sizes, widest first.\n"
    )
    name: str | None = Field(None, description="The name of the artist.\n")
    popularity: int | None = Field(
        None,
        deprecated=True,
        description="The popularity of the artist. The value will be between 0 and 100, with 100 being the most popular. The artist's popularity is calculated from the popularity of all the artist's tracks.\n",
    )
    type: ArtistObjectType | None = Field(None, description="The object type.\n")
    uri: str | None = Field(
        None,
        description="The [Spotify URI](/documentation/web-api/concepts/spotify-uris-ids) for the artist.\n",
    )


class SimplifiedArtist(SpotifyModel):
    external_urls: ExternalUrl | None = Field(
        None, description="Known external URLs for this artist.\n"
    )
    href: str | None = Field(
        None,
        description="A link to the Web API endpoint providing full details of the artist.\n",
    )
    id: str | None = Field(
        None,
        description="The [Spotify ID](/documentation/web-api/concepts/spotify-uris-ids) for the artist.\n",
    )
    name: str | None = Field(None, description="The name of the artist.\n")
    type: ArtistObjectType | None = Field(None, description="The object type.\n")
    uri: str | None = Field(
        None,
        description="The [Spotify URI](/documentation/web-api/concepts/spotify-uris-ids) for the artist.\n",
    )
