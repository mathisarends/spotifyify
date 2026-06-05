"""Create and replace a playlist using caller-supplied user access tokens."""

import asyncio
import os

from spotifyify import Spotifyify

TRACK_URIS = [
    "spotify:track:6rqhFgbbKwnb9MLmUQDhG6",
    "spotify:track:4uLU6hMCjMI75M1A2tKUQC",
]


async def create_playlist_for_user(
    spotify: Spotifyify,
    *,
    access_token: str,
    name: str,
) -> str:
    async with spotify.session(access_token=access_token):
        me = await spotify.users.me()
        playlist = await spotify.playlists.create(
            name,
            public=False,
            description=f"Created for {me.display_name or me.id}",
        )
        await spotify.playlists.replace(playlist.id, TRACK_URIS)
        await spotify.playlists.update(
            playlist.id,
            description="Created with a caller-supplied Spotify user token",
        )
        return playlist.id or ""


async def main() -> None:
    access_tokens = [
        token.strip()
        for token in os.environ["SPOTIFY_USER_ACCESS_TOKENS"].split(",")
        if token.strip()
    ]

    async with Spotifyify() as spotify:
        playlist_ids = await asyncio.gather(
            *(
                create_playlist_for_user(
                    spotify,
                    access_token=access_token,
                    name=f"BYOT Mix #{index}",
                )
                for index, access_token in enumerate(access_tokens, start=1)
            )
        )

    for playlist_id in playlist_ids:
        print(f"Created playlist: {playlist_id}")


if __name__ == "__main__":
    asyncio.run(main())
