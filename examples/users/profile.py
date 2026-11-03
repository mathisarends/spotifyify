"""Read the current user's profile and followed artists."""

import asyncio

from spotifyify import SpotifyClient, SpotifyScope


async def main() -> None:
    async with SpotifyClient(scopes=[SpotifyScope.USER_FOLLOW_READ]) as spotify:
        me = await spotify.users.me()
        print(f"Current user: {me.display_name} ({me.account_id or me.id})")

        following = await spotify.users.following(limit=5)
        selected = [artist for artist in following.items or [] if artist.id is not None]
        ids = [artist.id for artist in selected if artist.id is not None]
        checks = await spotify.users.check_following("artist", ids)
        for artist, follows in zip(selected, checks, strict=True):
            print(f"Following {artist.name}? {follows}")


if __name__ == "__main__":
    asyncio.run(main())
