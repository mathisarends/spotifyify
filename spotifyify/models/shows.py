"""Spotify shows response models; see schemas/source.json and docs/models.md."""

from __future__ import annotations

from .base import SpotifyModel
from pydantic import AwareDatetime
from pydantic import Field
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .common import Copyright
    from .common import ExternalUrl
    from .common import Image
    from .paging import PagingSimplifiedEpisode
    from .common import ShowObjectType


class ShowBase(SpotifyModel):
    available_markets: list[str] | None = Field(
        None,
        deprecated=True,
        description="A list of the countries in which the show can be played, identified by their [ISO 3166-1 alpha-2](http://en.wikipedia.org/wiki/ISO_3166-1_alpha-2) code.\n",
    )
    copyrights: list[Copyright] = Field(
        ..., description="The copyright statements of the show.\n"
    )
    description: str = Field(
        ...,
        description="A description of the show. HTML tags are stripped away from this field, use `html_description` field in case HTML tags are needed.\n",
    )
    html_description: str = Field(
        ...,
        description="A description of the show. This field may contain HTML tags.\n",
    )
    explicit: bool = Field(
        ...,
        description="Whether or not the show has explicit content (true = yes it does; false = no it does not OR unknown).\n",
    )
    external_urls: ExternalUrl = Field(
        ..., description="External URLs for this show.\n"
    )
    href: str = Field(
        ...,
        description="A link to the Web API endpoint providing full details of the show.\n",
    )
    id: str = Field(
        ...,
        description="The [Spotify ID](/documentation/web-api/concepts/spotify-uris-ids) for the show.\n",
    )
    images: list[Image] = Field(
        ..., description="The cover art for the show in various sizes, widest first.\n"
    )
    is_externally_hosted: bool | None = Field(
        None,
        description="True if all of the shows episodes are hosted outside of Spotify's CDN. This field might be `null` in some cases.\n",
    )
    languages: list[str] = Field(
        ...,
        description="A list of the languages used in the show, identified by their [ISO 639](https://en.wikipedia.org/wiki/ISO_639) code.\n",
    )
    media_type: str = Field(..., description="The media type of the show.\n")
    name: str = Field(..., description="The name of the episode.\n")
    publisher: str | None = Field(
        None, deprecated=True, description="The publisher of the show.\n"
    )
    type: ShowObjectType = Field(..., description="The object type.\n")
    uri: str = Field(
        ...,
        description="The [Spotify URI](/documentation/web-api/concepts/spotify-uris-ids) for the show.\n",
    )
    total_episodes: int = Field(
        ..., description="The total number of episodes in the show.\n"
    )


class SimplifiedShow(ShowBase):
    pass


class SavedShow(SpotifyModel):
    added_at: AwareDatetime | None = Field(
        None,
        description="The date and time the show was saved.\nTimestamps are returned in ISO 8601 format as Coordinated Universal Time (UTC) with a zero offset: YYYY-MM-DDTHH:MM:SSZ.\nIf the time is imprecise (for example, the date/time of an album release), an additional field indicates the precision; see for example, release_date in an album object.\n",
    )
    show: SimplifiedShow | None = Field(None, description="Information about the show.")


class Show(ShowBase):
    episodes: PagingSimplifiedEpisode = Field(
        ..., description="The episodes of the show.\n"
    )
