"""Spotify episodes response models; see schemas/source.json and docs/models.md."""

from __future__ import annotations

from typing import TYPE_CHECKING, Literal

from pydantic import AwareDatetime, Field

from .base import SpotifyModel

if TYPE_CHECKING:
    from .common import EpisodeObjectType, ExternalUrl, Image, ReleaseDatePrecision
    from .shows import SimplifiedShow


class EpisodeRestriction(SpotifyModel):
    reason: str | None = Field(
        None,
        description="The reason for the restriction. Supported values:\n- `market` - The content item is not available in the given market.\n- `product` - The content item is not available for the user's subscription type.\n- `explicit` - The content item is explicit and the user's account is set to not play explicit content.\n\nAdditional reasons may be added in the future.\n**Note**: If you use this field, make sure that your application safely handles unknown values.\n",
    )


class ResumePoint(SpotifyModel):
    fully_played: bool | None = Field(
        None,
        description="Whether or not the episode has been fully played by the user.\n",
    )
    resume_position_ms: int | None = Field(
        None,
        description="The user's most recent position in the episode in milliseconds.\n",
    )


class EpisodeBase(SpotifyModel):
    audio_preview_url: str | None = Field(
        None,
        deprecated=True,
        description="A URL to a 30 second preview (MP3 format) of the episode. `null` if not available.\n",
        examples=[
            "https://p.scdn.co/mp3-preview/2f37da1d4221f40b9d1a98cd191f4d6f1646ad17"
        ],
    )
    description: str = Field(
        ...,
        description="A description of the episode. HTML tags are stripped away from this field, use `html_description` field in case HTML tags are needed.\n",
        examples=[
            "A Spotify podcast sharing fresh insights on important topics of the moment—in a way only Spotify can. You’ll hear from experts in the music, podcast and tech industries as we discover and uncover stories about our work and the world around us.\n"
        ],
    )
    html_description: str = Field(
        ...,
        description="A description of the episode. This field may contain HTML tags.\n",
        examples=[
            "<p>A Spotify podcast sharing fresh insights on important topics of the moment—in a way only Spotify can. You’ll hear from experts in the music, podcast and tech industries as we discover and uncover stories about our work and the world around us.</p>\n"
        ],
    )
    duration_ms: int = Field(
        ..., description="The episode length in milliseconds.\n", examples=[1686230]
    )
    explicit: bool = Field(
        ...,
        description="Whether or not the episode has explicit content (true = yes it does; false = no it does not OR unknown).\n",
    )
    external_urls: ExternalUrl = Field(
        ..., description="External URLs for this episode.\n"
    )
    href: str = Field(
        ...,
        description="A link to the Web API endpoint providing full details of the episode.\n",
        examples=["https://api.spotify.com/v1/episodes/5Xt5DXGzch68nYYamXrNxZ"],
    )
    id: str = Field(
        ...,
        description="The [Spotify ID](/documentation/web-api/concepts/spotify-uris-ids) for the episode.\n",
        examples=["5Xt5DXGzch68nYYamXrNxZ"],
    )
    images: list[Image] = Field(
        ...,
        description="The cover art for the episode in various sizes, widest first.\n",
    )
    is_externally_hosted: bool | None = Field(
        None, description="True if the episode is hosted outside of Spotify's CDN.\n"
    )
    is_playable: bool = Field(
        ...,
        description="True if the episode is playable in the given market. Otherwise false.\n",
    )
    language: str | None = Field(
        None,
        deprecated=True,
        description="The language used in the episode, identified by a [ISO 639](https://en.wikipedia.org/wiki/ISO_639) code. This field is deprecated and might be removed in the future. Please use the `languages` field instead.\n",
        examples=["en"],
    )
    languages: list[str] = Field(
        ...,
        description="A list of the languages used in the episode, identified by their [ISO 639-1](https://en.wikipedia.org/wiki/ISO_639) code.\n",
        examples=[["fr", "en"]],
    )
    name: str = Field(
        ...,
        description="The name of the episode.\n",
        examples=[
            "Starting Your Own Podcast: Tips, Tricks, and Advice From Anchor Creators\n"
        ],
    )
    release_date: str = Field(
        ...,
        description='The date the episode was first released, for example `"1981-12-15"`. Depending on the precision, it might be shown as `"1981"` or `"1981-12"`.\n',
        examples=["1981-12-15"],
    )
    release_date_precision: ReleaseDatePrecision = Field(
        ...,
        description="The precision with which `release_date` value is known.\n",
        examples=["day"],
    )
    resume_point: ResumePoint | None = Field(
        None,
        description="The user's most recent position in the episode. Set if the supplied access token is a user token and has the scope 'user-read-playback-position'.\n",
    )
    type: EpisodeObjectType = Field(..., description="The object type.\n")
    uri: str = Field(
        ...,
        description="The [Spotify URI](/documentation/web-api/concepts/spotify-uris-ids) for the episode.\n",
        examples=["spotify:episode:0zLhl3WsOCQHbe1BPTiHgr"],
    )
    restrictions: EpisodeRestriction | None = Field(
        None,
        description="Included in the response when a content restriction is applied.\n",
    )


class Episode(EpisodeBase):
    show: SimplifiedShow = Field(
        ..., description="The show on which the episode belongs.\n"
    )
    type: Literal["episode", "EpisodeObject"]


class SimplifiedEpisode(EpisodeBase):
    pass


class SavedEpisode(SpotifyModel):
    added_at: AwareDatetime | None = Field(
        None,
        description="The date and time the episode was saved.\nTimestamps are returned in ISO 8601 format as Coordinated Universal Time (UTC) with a zero offset: YYYY-MM-DDTHH:MM:SSZ.\n",
    )
    episode: Episode | None = Field(None, description="Information about the episode.")
