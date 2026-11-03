"""Spotify playlists response models; see schemas/source.json and docs/models.md."""

from __future__ import annotations

from .base import SpotifyModel
from pydantic import AwareDatetime
from pydantic import Field
from typing import TYPE_CHECKING
from typing import Any

if TYPE_CHECKING:
    from .episodes import Episode
    from .common import ExternalUrl
    from .common import Image
    from .paging import PagingPlaylistItem
    from .users import PlaylistOwner
    from .users import PlaylistUser
    from .tracks import Track


class PlaylistItemsRef(SpotifyModel):
    href: str | None = Field(
        None,
        description="A link to the Web API endpoint where full details of the playlist's tracks can be retrieved.\n",
    )
    total: int | None = Field(None, description="Number of tracks in the playlist.\n")


class SimplifiedPlaylist(SpotifyModel):
    _legacy_aliases = {"tracks": "items"}
    collaborative: bool | None = Field(
        None,
        description="`true` if the owner allows other users to modify the playlist.\n",
    )
    description: str | None = Field(
        None,
        description="The playlist description. _Only returned for modified, verified playlists, otherwise_ `null`.\n",
    )
    external_urls: ExternalUrl | None = Field(
        None, description="Known external URLs for this playlist.\n"
    )
    href: str | None = Field(
        None,
        description="A link to the Web API endpoint providing full details of the playlist.\n",
    )
    id: str | None = Field(
        None,
        description="The [Spotify ID](/documentation/web-api/concepts/spotify-uris-ids) for the playlist.\n",
    )
    images: list[Image] | None = Field(
        None,
        description="Images for the playlist. The array may be empty or contain up to three images. The images are returned by size in descending order. See [Working with Playlists](/documentation/web-api/concepts/playlists). _**Note**: If returned, the source URL for the image (`url`) is temporary and will expire in less than a day._\n",
    )
    name: str | None = Field(None, description="The name of the playlist.\n")
    owner: PlaylistOwner | None = Field(
        None, description="The user who owns the playlist\n"
    )
    public: bool | None = Field(
        None,
        description="The playlist's public/private status (if it is added to the user's profile): `true` the playlist is public, `false` the playlist is private, `null` the playlist status is not relevant. For more about public/private status, see [Working with Playlists](/documentation/web-api/concepts/playlists)\n",
    )
    snapshot_id: str | None = Field(
        None,
        description="The version identifier for the current playlist. Can be supplied in other requests to target a specific playlist version\n",
    )
    items: PlaylistItemsRef | None = Field(
        None,
        description="A collection containing a link ( `href` ) to the Web API endpoint where full details of the playlist's items can be retrieved, along with the `total` number of items in the playlist. Note, a track object may be `null`. This can happen if a track is no longer available.\n",
    )
    type: str | None = Field(None, description='The object type: "playlist"\n')
    uri: str | None = Field(
        None,
        description="The [Spotify URI](/documentation/web-api/concepts/spotify-uris-ids) for the playlist.\n",
    )

    @property
    def tracks(self) -> PlaylistItemsRef | None:
        return self.items


class PlaylistItem(SpotifyModel):
    _legacy_aliases = {"track": "item"}
    added_at: AwareDatetime | None = Field(
        None,
        description="The date and time the track or episode was added. _**Note**: some very old playlists may return `null` in this field._\n",
    )
    added_by: PlaylistUser | None = Field(
        None,
        description="The Spotify user who added the track or episode. _**Note**: some very old playlists may return `null` in this field._\n",
    )
    is_local: bool | None = Field(
        None,
        description="Whether this track or episode is a [local file](/documentation/web-api/concepts/playlists/#local-files) or not.\n",
    )
    item: Track | Episode | None = Field(
        None,
        description="Information about the track or episode.",
        discriminator="type",
    )

    @property
    def track(self) -> Track | Episode | None:
        return self.item


class Playlist(SpotifyModel):
    _legacy_aliases = {"tracks": "items"}
    collaborative: bool | None = Field(
        None,
        description="`true` if the owner allows other users to modify the playlist.\n",
    )
    description: str | None = Field(
        None,
        description="The playlist description. _Only returned for modified, verified playlists, otherwise_ `null`.\n",
    )
    external_urls: ExternalUrl | None = Field(
        None, description="Known external URLs for this playlist.\n"
    )
    href: str | None = Field(
        None,
        description="A link to the Web API endpoint providing full details of the playlist.\n",
    )
    id: str | None = Field(
        None,
        description="The [Spotify ID](/documentation/web-api/concepts/spotify-uris-ids) for the playlist.\n",
    )
    images: list[Image] | None = Field(
        None,
        description="Images for the playlist. The array may be empty or contain up to three images. The images are returned by size in descending order. See [Working with Playlists](/documentation/web-api/concepts/playlists). _**Note**: If returned, the source URL for the image (`url`) is temporary and will expire in less than a day._\n",
    )
    name: str | None = Field(None, description="The name of the playlist.\n")
    owner: PlaylistOwner | None = Field(
        None, description="The user who owns the playlist\n"
    )
    public: bool | None = Field(
        None,
        description="The playlist's public/private status (if it is added to the user's profile): `true` the playlist is public, `false` the playlist is private, `null` the playlist status is not relevant. For more about public/private status, see [Working with Playlists](/documentation/web-api/concepts/playlists)\n",
    )
    snapshot_id: str | None = Field(
        None,
        description="The version identifier for the current playlist. Can be supplied in other requests to target a specific playlist version\n",
    )
    items: PagingPlaylistItem | None = Field(
        None,
        description="The items of the playlist. _**Note**: This field is only available for playlists owned by the current user or playlists the user is a collaborator of._\n",
    )
    type: str | None = Field(None, description='The object type: "playlist"\n')
    uri: str | None = Field(
        None,
        description="The [Spotify URI](/documentation/web-api/concepts/spotify-uris-ids) for the playlist.\n",
    )

    @property
    def tracks(self) -> PagingPlaylistItem | None:
        return self.items


class PlaylistItemProjection(SpotifyModel):
    """Selected item fields; no discriminator is required for partial responses."""

    _legacy_aliases = {"track": "item"}
    item: dict[str, Any] | None = None
    added_at: AwareDatetime | None = None


class PlaylistProjection(SpotifyModel):
    """A field-filtered playlist page whose paging metadata may be omitted."""

    items: list[PlaylistItemProjection] | None = None
    href: str | None = None
    limit: int | None = None
    offset: int | None = None
    total: int | None = None
    next: str | None = None
    previous: str | None = None
