"""Spotify audiobooks response models; see schemas/source.json and docs/models.md."""

from __future__ import annotations

from .base import SpotifyModel
from pydantic import Field
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .common import AudiobookObjectType
    from .common import ChapterObjectType
    from .common import Copyright
    from .common import ExternalUrl
    from .common import Image
    from .paging import PagingSimplifiedChapter
    from .common import ReleaseDatePrecision
    from .episodes import ResumePoint


class ChapterRestriction(SpotifyModel):
    reason: str | None = Field(
        None,
        description="The reason for the restriction. Supported values:\n- `market` - The content item is not available in the given market.\n- `product` - The content item is not available for the user's subscription type.\n- `explicit` - The content item is explicit and the user's account is set to not play explicit content.\n- `payment_required` - Payment is required to play the content item.\n\nAdditional reasons may be added in the future.\n**Note**: If you use this field, make sure that your application safely handles unknown values.\n",
    )


class Author(SpotifyModel):
    name: str | None = Field(None, description="The name of the author.\n")


class Narrator(SpotifyModel):
    name: str | None = Field(None, description="The name of the Narrator.\n")


class AudiobookBase(SpotifyModel):
    authors: list[Author] = Field(..., description="The author(s) for the audiobook.\n")
    available_markets: list[str] = Field(
        ...,
        deprecated=True,
        description="A list of the countries in which the audiobook can be played, identified by their [ISO 3166-1 alpha-2](http://en.wikipedia.org/wiki/ISO_3166-1_alpha-2) code.\n",
    )
    copyrights: list[Copyright] = Field(
        ..., description="The copyright statements of the audiobook.\n"
    )
    description: str = Field(
        ...,
        description="A description of the audiobook. HTML tags are stripped away from this field, use `html_description` field in case HTML tags are needed.\n",
    )
    html_description: str = Field(
        ...,
        description="A description of the audiobook. This field may contain HTML tags.\n",
    )
    edition: str | None = Field(
        None, description="The edition of the audiobook.\n", examples=["Unabridged"]
    )
    explicit: bool = Field(
        ...,
        description="Whether or not the audiobook has explicit content (true = yes it does; false = no it does not OR unknown).\n",
    )
    external_urls: ExternalUrl = Field(
        ..., description="External URLs for this audiobook.\n"
    )
    href: str = Field(
        ...,
        description="A link to the Web API endpoint providing full details of the audiobook.\n",
    )
    id: str = Field(
        ...,
        description="The [Spotify ID](/documentation/web-api/concepts/spotify-uris-ids) for the audiobook.\n",
    )
    images: list[Image] = Field(
        ...,
        description="The cover art for the audiobook in various sizes, widest first.\n",
    )
    languages: list[str] = Field(
        ...,
        description="A list of the languages used in the audiobook, identified by their [ISO 639](https://en.wikipedia.org/wiki/ISO_639) code.\n",
    )
    media_type: str = Field(..., description="The media type of the audiobook.\n")
    name: str = Field(..., description="The name of the audiobook.\n")
    narrators: list[Narrator] = Field(
        ..., description="The narrator(s) for the audiobook.\n"
    )
    publisher: str = Field(
        ..., deprecated=True, description="The publisher of the audiobook.\n"
    )
    type: AudiobookObjectType = Field(..., description="The object type.\n")
    uri: str = Field(
        ...,
        description="The [Spotify URI](/documentation/web-api/concepts/spotify-uris-ids) for the audiobook.\n",
    )
    total_chapters: int = Field(
        ..., description="The number of chapters in this audiobook.\n"
    )


class SimplifiedAudiobook(AudiobookBase):
    pass


class ChapterBase(SpotifyModel):
    audio_preview_url: str | None = Field(
        None,
        deprecated=True,
        description="A URL to a 30 second preview (MP3 format) of the chapter. `null` if not available.\n",
        examples=[
            "https://p.scdn.co/mp3-preview/2f37da1d4221f40b9d1a98cd191f4d6f1646ad17"
        ],
    )
    available_markets: list[str] | None = Field(
        None,
        deprecated=True,
        description="A list of the countries in which the chapter can be played, identified by their [ISO 3166-1 alpha-2](http://en.wikipedia.org/wiki/ISO_3166-1_alpha-2) code.\n",
    )
    chapter_number: int = Field(
        ..., description="The number of the chapter\n", examples=[1]
    )
    description: str = Field(
        ...,
        description="A description of the chapter. HTML tags are stripped away from this field, use `html_description` field in case HTML tags are needed.\n",
        examples=[
            "We kept on ascending, with occasional periods of quick descent, but in the main always ascending. Suddenly, I became conscious of the fact that the driver was in the act of pulling up the horses in the courtyard of a vast ruined castle, from whose tall black windows came no ray of light, and whose broken battlements showed a jagged line against the moonlit sky.\n"
        ],
    )
    html_description: str = Field(
        ...,
        description="A description of the chapter. This field may contain HTML tags.\n",
        examples=[
            "<p>We kept on ascending, with occasional periods of quick descent, but in the main always ascending. Suddenly, I became conscious of the fact that the driver was in the act of pulling up the horses in the courtyard of a vast ruined castle, from whose tall black windows came no ray of light, and whose broken battlements showed a jagged line against the moonlit sky.</p>\n"
        ],
    )
    duration_ms: int = Field(
        ..., description="The chapter length in milliseconds.\n", examples=[1686230]
    )
    explicit: bool = Field(
        ...,
        description="Whether or not the chapter has explicit content (true = yes it does; false = no it does not OR unknown).\n",
    )
    external_urls: ExternalUrl = Field(
        ..., description="External URLs for this chapter.\n"
    )
    href: str = Field(
        ...,
        description="A link to the Web API endpoint providing full details of the chapter.\n",
        examples=["https://api.spotify.com/v1/episodes/5Xt5DXGzch68nYYamXrNxZ"],
    )
    id: str = Field(
        ...,
        description="The [Spotify ID](/documentation/web-api/concepts/spotify-uris-ids) for the chapter.\n",
        examples=["5Xt5DXGzch68nYYamXrNxZ"],
    )
    images: list[Image] = Field(
        ...,
        description="The cover art for the chapter in various sizes, widest first.\n",
    )
    is_playable: bool = Field(
        ...,
        description="True if the chapter is playable in the given market. Otherwise false.\n",
    )
    languages: list[str] = Field(
        ...,
        description="A list of the languages used in the chapter, identified by their [ISO 639-1](https://en.wikipedia.org/wiki/ISO_639) code.\n",
        examples=[["fr", "en"]],
    )
    name: str = Field(
        ...,
        description="The name of the chapter.\n",
        examples=[
            "Starting Your Own Podcast: Tips, Tricks, and Advice From Anchor Creators\n"
        ],
    )
    release_date: str = Field(
        ...,
        description='The date the chapter was first released, for example `"1981-12-15"`. Depending on the precision, it might be shown as `"1981"` or `"1981-12"`.\n',
        examples=["1981-12-15"],
    )
    release_date_precision: ReleaseDatePrecision = Field(
        ...,
        description="The precision with which `release_date` value is known.\n",
        examples=["day"],
    )
    resume_point: ResumePoint | None = Field(
        None,
        description="The user's most recent position in the chapter. Set if the supplied access token is a user token and has the scope 'user-read-playback-position'.\n",
    )
    type: ChapterObjectType = Field(..., description="The object type.\n")
    uri: str = Field(
        ...,
        description="The [Spotify URI](/documentation/web-api/concepts/spotify-uris-ids) for the chapter.\n",
        examples=["spotify:episode:0zLhl3WsOCQHbe1BPTiHgr"],
    )
    restrictions: ChapterRestriction | None = Field(
        None,
        description="Included in the response when a content restriction is applied.\n",
    )


class Chapter(ChapterBase):
    audiobook: SimplifiedAudiobook = Field(
        ..., description="The audiobook for which the chapter belongs.\n"
    )


class SimplifiedChapter(ChapterBase):
    pass


class Audiobook(AudiobookBase):
    chapters: PagingSimplifiedChapter = Field(
        ..., description="The chapters of the audiobook.\n"
    )
