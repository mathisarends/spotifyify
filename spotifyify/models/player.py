"""Spotify player response models; see schemas/source.json and docs/models.md."""

from __future__ import annotations

from typing import TYPE_CHECKING

from pydantic import Field, RootModel

from .base import SpotifyModel
from .episodes import Episode
from .tracks import Track

if TYPE_CHECKING:
    from .common import ExternalUrl, VolumePercent


class Disallows(SpotifyModel):
    interrupting_playback: bool | None = Field(
        None, description="Interrupting playback. Optional field."
    )
    pausing: bool | None = Field(None, description="Pausing. Optional field.")
    resuming: bool | None = Field(None, description="Resuming. Optional field.")
    seeking: bool | None = Field(
        None, description="Seeking playback location. Optional field."
    )
    skipping_next: bool | None = Field(
        None, description="Skipping to the next context. Optional field."
    )
    skipping_prev: bool | None = Field(
        None, description="Skipping to the previous context. Optional field."
    )
    toggling_repeat_context: bool | None = Field(
        None, description="Toggling repeat context flag. Optional field."
    )
    toggling_shuffle: bool | None = Field(
        None, description="Toggling shuffle flag. Optional field."
    )
    toggling_repeat_track: bool | None = Field(
        None, description="Toggling repeat track flag. Optional field."
    )
    transferring_playback: bool | None = Field(
        None, description="Transfering playback between devices. Optional field."
    )


class Device(SpotifyModel):
    id: str | None = Field(
        None,
        description="The device ID. This ID is unique and persistent to some extent. However, this is not guaranteed and any cached `device_id` should periodically be cleared out and refetched as necessary.",
    )
    is_active: bool | None = Field(
        None, description="If this device is the currently active device."
    )
    is_private_session: bool | None = Field(
        None, description="If this device is currently in a private session."
    )
    is_restricted: bool | None = Field(
        None,
        description='Whether controlling this device is restricted. At present if this is "true" then no Web API commands will be accepted by this device.',
    )
    name: str | None = Field(
        None,
        description='A human-readable name for the device. Some devices have a name that the user can configure (e.g. \\"Loudest speaker\\") and some devices have a generic name associated with the manufacturer or device model.',
        examples=["Kitchen speaker"],
    )
    type: str | None = Field(
        None,
        description='Device type, such as "computer", "smartphone" or "speaker".',
        examples=["computer"],
    )
    volume_percent: VolumePercent | None = Field(
        None, description="The current volume in percent.", examples=[59]
    )
    supports_volume: bool | None = Field(
        None, description="If this device can be used to set the volume."
    )


class Context(SpotifyModel):
    type: str | None = Field(
        None,
        description='The object type, e.g. "artist", "playlist", "album", "show".\n',
    )
    href: str | None = Field(
        None,
        description="A link to the Web API endpoint providing full details of the track.",
    )
    external_urls: ExternalUrl | None = Field(
        None, description="External URLs for this context."
    )
    uri: str | None = Field(
        None,
        description="The [Spotify URI](/documentation/web-api/concepts/spotify-uris-ids) for the context.\n",
    )


class Queue(RootModel[Track | Episode]):
    root: Track | Episode = Field(..., discriminator="type")


class PlayerQueue(SpotifyModel):
    currently_playing: Track | Episode | None = Field(
        None,
        description="The currently playing track or episode. Can be `null`.",
        discriminator="type",
    )
    queue: list[Track | Episode] | None = Field(
        None, description="The tracks or episodes in the queue. Can be empty."
    )


class PlaybackState(SpotifyModel):
    device: Device | None = Field(
        None, description="The device that is currently active.\n"
    )
    repeat_state: str | None = Field(None, description="off, track, context")
    shuffle_state: bool | None = Field(None, description="If shuffle is on or off.")
    context: Context | None = Field(
        None, description="A Context Object. Can be `null`."
    )
    timestamp: int | None = Field(
        None,
        description="Unix Millisecond Timestamp when playback state was last changed (play, pause, skip, scrub, new song, etc.).",
    )
    progress_ms: int | None = Field(
        None,
        description="Progress into the currently playing track or episode. Can be `null`.",
    )
    is_playing: bool | None = Field(
        None, description="If something is currently playing, return `true`."
    )
    item: Track | Episode | None = Field(
        None,
        description="The currently playing track or episode. Can be `null`.",
        discriminator="type",
    )
    currently_playing_type: str | None = Field(
        None,
        description="The object type of the currently playing item. Can be one of `track`, `episode`, `ad` or `unknown`.\n",
    )
    actions: Disallows | None = Field(
        None,
        description="Allows to update the user interface based on which playback actions are available within the current context.\n",
    )
