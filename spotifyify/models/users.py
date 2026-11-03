"""Spotify users response models; see schemas/source.json and docs/models.md."""

from __future__ import annotations

from .base import SpotifyModel
from pydantic import Field
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .common import ExplicitContentSettings
    from .common import ExternalUrl
    from .common import Followers
    from .common import Image
    from .common import PlaylistUserObjectType
    from .common import UserObjectType


class User(SpotifyModel):
    account_id: str | None = None
    country: str | None = Field(
        None,
        deprecated=True,
        description="The country of the user, as set in the user's account profile. An [ISO 3166-1 alpha-2 country code](http://en.wikipedia.org/wiki/ISO_3166-1_alpha-2). _This field is only available when the current user has granted access to the [user-read-private](/documentation/web-api/concepts/scopes/#list-of-scopes) scope._\n",
    )
    display_name: str | None = Field(
        None,
        description="The name displayed on the user's profile. `null` if not available.\n",
    )
    email: str | None = Field(
        None,
        deprecated=True,
        description="The user's email address, as entered by the user when creating their account. _**Important!** This email address is unverified; there is no proof that it actually belongs to the user._ _This field is only available when the current user has granted access to the [user-read-email](/documentation/web-api/concepts/scopes/#list-of-scopes) scope._\n",
    )
    explicit_content: ExplicitContentSettings | None = Field(
        None,
        deprecated=True,
        description="The user's explicit content settings. _This field is only available when the current user has granted access to the [user-read-private](/documentation/web-api/concepts/scopes/#list-of-scopes) scope._\n",
    )
    external_urls: ExternalUrl | None = Field(
        None, description="Known external URLs for this user."
    )
    followers: Followers | None = Field(
        None,
        deprecated=True,
        description="Information about the followers of the user.",
    )
    href: str | None = Field(
        None, description="A link to the Web API endpoint for this user.\n"
    )
    id: str | None = Field(
        None,
        description="The [Spotify user ID](/documentation/web-api/concepts/spotify-uris-ids) for the user.\n",
    )
    images: list[Image] | None = Field(None, description="The user's profile image.")
    product: str | None = Field(
        None,
        deprecated=True,
        description='The user\'s Spotify subscription level: "premium", "free", etc. (The subscription level "open" can be considered the same as "free".) _This field is only available when the current user has granted access to the [user-read-private](/documentation/web-api/concepts/scopes/#list-of-scopes) scope._\n',
    )
    type: str | None = Field(None, description='The object type: "user"\n')
    uri: str | None = Field(
        None,
        description="The [Spotify URI](/documentation/web-api/concepts/spotify-uris-ids) for the user.\n",
    )


class PublicUser(SpotifyModel):
    display_name: str | None = Field(
        None,
        description="The name displayed on the user's profile. `null` if not available.\n",
    )
    external_urls: ExternalUrl | None = Field(
        None, description="Known public external URLs for this user.\n"
    )
    followers: Followers | None = Field(
        None,
        deprecated=True,
        description="Information about the followers of this user.\n",
    )
    href: str | None = Field(
        None, description="A link to the Web API endpoint for this user.\n"
    )
    id: str | None = Field(
        None,
        description="The [Spotify user ID](/documentation/web-api/concepts/spotify-uris-ids) for this user.\n",
    )
    images: list[Image] | None = Field(None, description="The user's profile image.\n")
    type: UserObjectType | None = Field(None, description="The object type.\n")
    uri: str | None = Field(
        None,
        description="The [Spotify URI](/documentation/web-api/concepts/spotify-uris-ids) for this user.\n",
    )


class PlaylistUser(SpotifyModel):
    external_urls: ExternalUrl | None = Field(
        None, description="Known public external URLs for this user.\n"
    )
    href: str | None = Field(
        None, description="A link to the Web API endpoint for this user.\n"
    )
    id: str | None = Field(
        None,
        description="The [Spotify user ID](/documentation/web-api/concepts/spotify-uris-ids) for this user.\n",
    )
    type: PlaylistUserObjectType | None = Field(None, description="The object type.\n")
    uri: str | None = Field(
        None,
        description="The [Spotify URI](/documentation/web-api/concepts/spotify-uris-ids) for this user.\n",
    )


class PlaylistOwner(PlaylistUser):
    display_name: str | None = Field(
        None,
        description="The name displayed on the user's profile. `null` if not available.\n",
    )
