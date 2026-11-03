"""Spotify tracks response models; see schemas/source.json and docs/models.md."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, Literal

from pydantic import AwareDatetime, Field

from .base import SpotifyModel

if TYPE_CHECKING:
    from .albums import SimplifiedAlbum
    from .artists import SimplifiedArtist
    from .common import ExternalId, ExternalUrl, TrackRestriction
    from .player import Context


class LinkedTrack(SpotifyModel):
    external_urls: ExternalUrl | None = Field(
        None, description="Known external URLs for this track.\n"
    )
    href: str | None = Field(
        None,
        description="A link to the Web API endpoint providing full details of the track.\n",
    )
    id: str | None = Field(
        None,
        description="The [Spotify ID](/documentation/web-api/concepts/spotify-uris-ids) for the track.\n",
    )
    type: str | None = Field(None, description='The object type: "track".\n')
    uri: str | None = Field(
        None,
        description="The [Spotify URI](/documentation/web-api/concepts/spotify-uris-ids) for the track.\n",
    )


class SimplifiedTrack(SpotifyModel):
    artists: list[SimplifiedArtist] | None = Field(
        None,
        description="The artists who performed the track. Each artist object includes a link in `href` to more detailed information about the artist.",
    )
    available_markets: list[str] | None = Field(
        None,
        deprecated=True,
        description="A list of the countries in which the track can be played, identified by their [ISO 3166-1 alpha-2](http://en.wikipedia.org/wiki/ISO_3166-1_alpha-2) code.\n",
    )
    disc_number: int | None = Field(
        None,
        description="The disc number (usually `1` unless the album consists of more than one disc).",
    )
    duration_ms: int | None = Field(
        None, description="The track length in milliseconds."
    )
    explicit: bool | None = Field(
        None,
        description="Whether or not the track has explicit lyrics ( `true` = yes it does; `false` = no it does not OR unknown).",
    )
    external_urls: ExternalUrl | None = Field(
        None, description="External URLs for this track.\n"
    )
    href: str | None = Field(
        None,
        description="A link to the Web API endpoint providing full details of the track.",
    )
    id: str | None = Field(
        None,
        description="The [Spotify ID](/documentation/web-api/concepts/spotify-uris-ids) for the track.\n",
    )
    is_playable: bool | None = Field(
        None,
        description="Part of the response when [Track Relinking](/documentation/web-api/concepts/track-relinking/) is applied. If `true`, the track is playable in the given market. Otherwise `false`.\n",
    )
    linked_from: LinkedTrack | None = Field(
        None,
        deprecated=True,
        description="Part of the response when [Track Relinking](/documentation/web-api/concepts/track-relinking/) is applied and is only part of the response if the track linking, in fact, exists. The requested track has been replaced with a different track. The track in the `linked_from` object contains information about the originally requested track.",
    )
    restrictions: TrackRestriction | None = Field(
        None,
        description="Included in the response when a content restriction is applied.\n",
    )
    name: str | None = Field(None, description="The name of the track.")
    preview_url: str | None = Field(
        None,
        deprecated=True,
        description="A URL to a 30 second preview (MP3 format) of the track.\n",
    )
    track_number: int | None = Field(
        None,
        description="The number of the track. If an album has several discs, the track number is the number on the specified disc.\n",
    )
    type: str | None = Field(None, description='The object type: "track".\n')
    uri: str | None = Field(
        None,
        description="The [Spotify URI](/documentation/web-api/concepts/spotify-uris-ids) for the track.\n",
    )
    is_local: bool | None = Field(
        None, description="Whether or not the track is from a local file.\n"
    )


class Track(SpotifyModel):
    album: SimplifiedAlbum | None = Field(
        None,
        description="The album on which the track appears. The album object includes a link in `href` to full information about the album.\n",
    )
    artists: list[SimplifiedArtist] | None = Field(
        None,
        description="The artists who performed the track. Each artist object includes a link in `href` to more detailed information about the artist.\n",
    )
    available_markets: list[str] | None = Field(
        None,
        deprecated=True,
        description="A list of the countries in which the track can be played, identified by their [ISO 3166-1 alpha-2](http://en.wikipedia.org/wiki/ISO_3166-1_alpha-2) code.\n",
    )
    disc_number: int | None = Field(
        None,
        description="The disc number (usually `1` unless the album consists of more than one disc).\n",
    )
    duration_ms: int | None = Field(
        None, description="The track length in milliseconds.\n"
    )
    explicit: bool | None = Field(
        None,
        description="Whether or not the track has explicit lyrics ( `true` = yes it does; `false` = no it does not OR unknown).\n",
    )
    external_ids: ExternalId | None = Field(
        None, description="Known external IDs for the track.\n"
    )
    external_urls: ExternalUrl | None = Field(
        None, description="Known external URLs for this track.\n"
    )
    href: str | None = Field(
        None,
        description="A link to the Web API endpoint providing full details of the track.\n",
    )
    id: str | None = Field(
        None,
        description="The [Spotify ID](/documentation/web-api/concepts/spotify-uris-ids) for the track.\n",
    )
    is_playable: bool | None = Field(
        None,
        description="Part of the response when [Track Relinking](/documentation/web-api/concepts/track-relinking) is applied. If `true`, the track is playable in the given market. Otherwise `false`.\n",
    )
    linked_from: dict[str, Any] | None = Field(
        None,
        deprecated=True,
        description="Part of the response when [Track Relinking](/documentation/web-api/concepts/track-relinking) is applied, and the requested track has been replaced with different track. The track in the `linked_from` object contains information about the originally requested track.\n",
    )
    restrictions: TrackRestriction | None = Field(
        None,
        description="Included in the response when a content restriction is applied.\n",
    )
    name: str | None = Field(None, description="The name of the track.\n")
    popularity: int | None = Field(
        None,
        deprecated=True,
        description="The popularity of the track. The value will be between 0 and 100, with 100 being the most popular.<br/>The popularity of a track is a value between 0 and 100, with 100 being the most popular. The popularity is calculated by algorithm and is based, in the most part, on the total number of plays the track has had and how recent those plays are.<br/>Generally speaking, songs that are being played a lot now will have a higher popularity than songs that were played a lot in the past. Duplicate tracks (e.g. the same track from a single and an album) are rated independently. Artist and album popularity is derived mathematically from track popularity. _**Note**: the popularity value may lag actual popularity by a few days: the value is not updated in real time._\n",
    )
    preview_url: str | None = Field(
        None,
        deprecated=True,
        description="A link to a 30 second preview (MP3 format) of the track. Can be `null`\n",
    )
    track_number: int | None = Field(
        None,
        description="The number of the track. If an album has several discs, the track number is the number on the specified disc.\n",
    )
    type: Literal["track"] = Field(..., description='The object type: "track".\n')
    uri: str | None = Field(
        None,
        description="The [Spotify URI](/documentation/web-api/concepts/spotify-uris-ids) for the track.\n",
    )
    is_local: bool | None = Field(
        None, description="Whether or not the track is from a local file.\n"
    )


class PlayHistory(SpotifyModel):
    track: Track | None = Field(None, description="The track the user listened to.")
    played_at: AwareDatetime | None = Field(
        None, description="The date and time the track was played."
    )
    context: Context | None = Field(
        None, description="The context the track was played from."
    )


class SavedTrack(SpotifyModel):
    added_at: AwareDatetime | None = Field(
        None,
        description="The date and time the track was saved.\nTimestamps are returned in ISO 8601 format as Coordinated Universal Time (UTC) with a zero offset: YYYY-MM-DDTHH:MM:SSZ.\nIf the time is imprecise (for example, the date/time of an album release), an additional field indicates the precision; see for example, release_date in an album object.\n",
    )
    track: Track | None = Field(None, description="Information about the track.")
