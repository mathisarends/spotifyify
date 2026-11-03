"""Spotify albums response models; see schemas/source.json and docs/models.md."""

from __future__ import annotations

from .base import SpotifyModel
from pydantic import AwareDatetime
from pydantic import Field
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .common import AlbumGroup
    from .common import AlbumObjectType
    from .common import AlbumRestriction
    from .common import AlbumType
    from .common import Copyright
    from .common import ExternalId
    from .common import ExternalUrl
    from .common import Image
    from .paging import PagingSimplifiedTrack
    from .common import ReleaseDatePrecision
    from .artists import SimplifiedArtist


class AlbumBase(SpotifyModel):
    album_type: AlbumType = Field(
        ..., description="The type of the album.\n", examples=["compilation"]
    )
    total_tracks: int = Field(
        ..., description="The number of tracks in the album.", examples=[9]
    )
    available_markets: list[str] | None = Field(
        None,
        deprecated=True,
        description="The markets in which the album is available: [ISO 3166-1 alpha-2 country codes](http://en.wikipedia.org/wiki/ISO_3166-1_alpha-2). _**NOTE**: an album is considered available in a market when at least 1 of its tracks is available in that market._\n",
        examples=[["CA", "BR", "IT"]],
    )
    external_urls: ExternalUrl = Field(
        ..., description="Known external URLs for this album.\n"
    )
    href: str = Field(
        ...,
        description="A link to the Web API endpoint providing full details of the album.\n",
    )
    id: str = Field(
        ...,
        description="The [Spotify ID](/documentation/web-api/concepts/spotify-uris-ids) for the album.\n",
        examples=["2up3OPMp9Tb4dAKM2erWXQ"],
    )
    images: list[Image] = Field(
        ..., description="The cover art for the album in various sizes, widest first.\n"
    )
    name: str = Field(
        ...,
        description="The name of the album. In case of an album takedown, the value may be an empty string.\n",
    )
    release_date: str = Field(
        ...,
        description="The date the album was first released.\n",
        examples=["1981-12"],
    )
    release_date_precision: ReleaseDatePrecision = Field(
        ...,
        description="The precision with which `release_date` value is known.\n",
        examples=["year"],
    )
    restrictions: AlbumRestriction | None = Field(
        None,
        description="Included in the response when a content restriction is applied.\n",
    )
    type: AlbumObjectType = Field(..., description="The object type.\n")
    uri: str = Field(
        ...,
        description="The [Spotify URI](/documentation/web-api/concepts/spotify-uris-ids) for the album.\n",
        examples=["spotify:album:2up3OPMp9Tb4dAKM2erWXQ"],
    )


class SimplifiedAlbum(AlbumBase):
    artists: list[SimplifiedArtist] = Field(
        ...,
        description="The artists of the album. Each artist object includes a link in `href` to more detailed information about the artist.\n",
    )


class ArtistDiscographyAlbum(SimplifiedAlbum):
    album_group: AlbumGroup | None = Field(
        None,
        deprecated=True,
        description="This field describes the relationship between the artist and the album.\n",
        examples=["compilation"],
    )


class Album(AlbumBase):
    artists: list[SimplifiedArtist] = Field(
        ...,
        description="The artists of the album. Each artist object includes a link in `href` to more detailed information about the artist.\n",
    )
    tracks: PagingSimplifiedTrack = Field(..., description="The tracks of the album.\n")
    copyrights: list[Copyright] = Field(
        ..., description="The copyright statements of the album.\n"
    )
    external_ids: ExternalId = Field(
        ..., description="Known external IDs for the album.\n"
    )
    genres: list[str] = Field(
        ...,
        deprecated=True,
        description="**Deprecated** The array is always empty.\n",
        examples=[[]],
    )
    label: str | None = Field(
        None, deprecated=True, description="The label associated with the album.\n"
    )
    popularity: int | None = Field(
        None,
        deprecated=True,
        description="The popularity of the album. The value will be between 0 and 100, with 100 being the most popular.\n",
    )


class SavedAlbum(SpotifyModel):
    added_at: AwareDatetime | None = Field(
        None,
        description="The date and time the album was saved\nTimestamps are returned in ISO 8601 format as Coordinated Universal Time (UTC) with a zero offset: YYYY-MM-DDTHH:MM:SSZ.\nIf the time is imprecise (for example, the date/time of an album release), an additional field indicates the precision; see for example, release_date in an album object.\n",
    )
    album: Album | None = Field(None, description="Information about the album.")
