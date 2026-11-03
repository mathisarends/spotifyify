"""Spotify common response models; see schemas/source.json and docs/models.md."""

from __future__ import annotations

from .base import SpotifyModel
from enum import Enum
from pydantic import Field
from typing import Annotated


HTTPStatusCode = Annotated[int, Field(ge=400, le=599)]


Confidence = Annotated[float, Field(ge=0.0, le=1.0)]


TimeSignatureValue = Annotated[int, Field(ge=3, le=7)]


MusicalKeyValue = Annotated[int, Field(ge=-1, le=11)]


VolumePercent = Annotated[int, Field(ge=0, le=100)]


class TrackRestriction(SpotifyModel):
    reason: str | None = Field(
        None,
        description="The reason for the restriction. Supported values:\n- `market` - The content item is not available in the given market.\n- `product` - The content item is not available for the user's subscription type.\n- `explicit` - The content item is explicit and the user's account is set to not play explicit content.\n\nAdditional reasons may be added in the future.\n**Note**: If you use this field, make sure that your application safely handles unknown values.\n",
    )


class Reason(Enum):
    market = "market"
    product = "product"
    explicit = "explicit"


class AlbumRestriction(SpotifyModel):
    reason: str | None = Field(
        None,
        description="The reason for the restriction. Albums may be restricted if the content is not available in a given market, to the user's subscription type, or when the user's account is set to not play explicit content.\nAdditional reasons may be added in the future.\n",
    )


class ArtistObjectType(Enum):
    artist = "artist"


class Error(SpotifyModel):
    status: HTTPStatusCode = Field(
        ...,
        description="The HTTP status code (also returned in the response header; see [Response Status Codes](/documentation/web-api/concepts/api-calls#response-status-codes) for more information).\n",
    )
    message: str = Field(
        ..., description="A short description of the cause of the error.\n"
    )


class UserObjectType(Enum):
    user = "user"


class Mode1(Enum):
    number__1 = -1
    number_0 = 0
    number_1 = 1


class PlaylistUserObjectType(Enum):
    user = "user"


class TrackObjectType(Enum):
    track = "track"


class ReleaseDatePrecision(Enum):
    year = "year"
    month = "month"
    day = "day"


class EpisodeObjectType(Enum):
    episode = "episode"


class ShowObjectType(Enum):
    show = "show"


class AudiobookObjectType(Enum):
    audiobook = "audiobook"


class AlbumType(Enum):
    album = "album"
    single = "single"
    compilation = "compilation"
    ep = "ep"


class AlbumObjectType(Enum):
    album = "album"


class AlbumGroup(Enum):
    album = "album"
    single = "single"
    compilation = "compilation"
    appears_on = "appears_on"


class ChapterObjectType(Enum):
    episode = "episode"


class Copyright(SpotifyModel):
    text: str | None = Field(None, description="The copyright text for this content.\n")
    type: str | None = Field(
        None,
        description="The type of copyright: `C` = the copyright, `P` = the sound recording (performance) copyright.\n",
    )


class ExternalId(SpotifyModel):
    isrc: str | None = Field(
        None,
        description="[International Standard Recording Code](http://en.wikipedia.org/wiki/International_Standard_Recording_Code)\n",
    )
    ean: str | None = Field(
        None,
        description="[International Article Number](http://en.wikipedia.org/wiki/International_Article_Number_%28EAN%29)\n",
    )
    upc: str | None = Field(
        None,
        description="[Universal Product Code](http://en.wikipedia.org/wiki/Universal_Product_Code)\n",
    )


class ExternalUrl(SpotifyModel):
    spotify: str | None = Field(
        None,
        description="The [Spotify URL](/documentation/web-api/concepts/spotify-uris-ids) for the object.\n",
    )


class Followers(SpotifyModel):
    href: str | None = Field(
        None,
        description="This will always be set to null, as the Web API does not support it at the moment.\n",
    )
    total: int | None = Field(None, description="The total number of followers.\n")


class Image(SpotifyModel):
    url: str = Field(
        ...,
        description="The source URL of the image.\n",
        examples=["https://i.scdn.co/image/ab67616d00001e02ff9ca10b55ce82ae553c8228\n"],
    )
    height: int | None = Field(
        None, description="The image height in pixels.\n", examples=[300]
    )
    width: int | None = Field(
        None, description="The image width in pixels.\n", examples=[300]
    )


class ExplicitContentSettings(SpotifyModel):
    filter_enabled: bool | None = Field(
        None,
        description="When `true`, indicates that explicit content should not be played.\n",
    )
    filter_locked: bool | None = Field(
        None,
        description="When `true`, indicates that the explicit content setting is locked and can't be changed by the user.\n",
    )


class Category(SpotifyModel):
    href: str = Field(
        ...,
        description="A link to the Web API endpoint returning full details of the category.\n",
    )
    icons: list[Image] = Field(
        ..., description="The category icon, in various sizes.\n"
    )
    id: str = Field(
        ...,
        description="The [Spotify category ID](/documentation/web-api/concepts/spotify-uris-ids) of the category.\n",
        examples=["equal"],
    )
    name: str = Field(
        ..., description="The name of the category.\n", examples=["EQUAL"]
    )
