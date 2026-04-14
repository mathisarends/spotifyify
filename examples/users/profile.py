"""Smoke test for the users namespace: me, get, following, check_following."""

import asyncio
from spotifyify import Spotifyify


async def main() -> None:
    async with Spotifyify() as sp:
        me = await sp.users.me()
        print(f"Current user: {me.display_name} ({me.id})")
        print(f"  Country: {me.country}")
        print(f"  Product: {me.product}")
        print(f"  Followers: {me.followers.total if me.followers else 0}")

        public = await sp.users.get(me.id)
        print(f"\nPublic profile for '{public.display_name}':")
        print(f"  Followers: {public.followers.total if public.followers else 0}")

        following = await sp.users.following(limit=5)
        print(f"\nFollowed artists ({following.total} total):")
        for artist in following.items:
            print(f"  {artist.name}")

        if following.items:
            ids = [a.id for a in following.items[:3]]
            checks = await sp.users.check_following(type="artist", ids=ids)
            for artist, is_following in zip(following.items[:3], checks):
                print(f"  Following {artist.name}? {is_following}")


asyncio.run(main())
