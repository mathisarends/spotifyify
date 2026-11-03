from collections.abc import AsyncIterator, Iterable
from typing import Any

from spotifyify.batching import chunks
from spotifyify.config import ApiMode
from spotifyify.exceptions import SpotifyResponseError
from spotifyify.http.response import list_response, object_response, validate_model
from spotifyify.namespaces.base import Resource
from spotifyify.pagination import iter_cursor_items
from spotifyify.schemas import Artist, CursorPagingSimplifiedArtist, PublicUser, User
from spotifyify.utils import coalesce_items
from spotifyify.validation import page as validate_page
from spotifyify.validation import spotify_id as validate_id


class Users(Resource):
    async def me(self) -> User:
        data = await self._http.get("/me")
        return validate_model(User, data)

    async def get(self, user_id: str) -> PublicUser:
        user_id = validate_id(user_id)
        self._require_extended("Other user profiles")
        data = await self._http.get(f"/users/{user_id}", require_user=False)
        return validate_model(PublicUser, data)

    async def following(
        self,
        *,
        type: str = "artist",
        limit: int = 20,
        after: str | None = None,
    ) -> CursorPagingSimplifiedArtist:
        validate_page(limit)
        if type != "artist":
            raise ValueError("following supports only type=artist")
        params: dict[str, str | int] = {"type": type, "limit": limit}
        if after:
            params["after"] = after
        data = await self._http.get("/me/following", params=params)
        artists = object_response(object_response(data).get("artists"))
        return validate_model(CursorPagingSimplifiedArtist, artists)

    async def follow(self, type: str, ids: Iterable[str]) -> None:
        if type not in {"artist", "user"}:
            raise ValueError("type must be artist or user")
        values = [validate_id(value) for value in coalesce_items(ids)]
        if self._http.api_mode == ApiMode.DEVELOPMENT:
            await self._library_write(type, values, remove=False)
        else:
            for batch in chunks(values, 50):
                await self._http.put(
                    "/me/following", params={"type": type}, payload={"ids": batch}
                )

    async def unfollow(self, type: str, ids: Iterable[str]) -> None:
        if type not in {"artist", "user"}:
            raise ValueError("type must be artist or user")
        values = [validate_id(value) for value in coalesce_items(ids)]
        if self._http.api_mode == ApiMode.DEVELOPMENT:
            await self._library_write(type, values, remove=True)
        else:
            for batch in chunks(values, 50):
                await self._http.delete(
                    "/me/following", params={"type": type}, payload={"ids": batch}
                )

    async def check_following(self, type: str, ids: Iterable[str]) -> list[bool]:
        if type not in {"artist", "user"}:
            raise ValueError("type must be artist or user")
        values = [validate_id(value) for value in coalesce_items(ids)]
        if self._http.api_mode == ApiMode.DEVELOPMENT:
            return await self._library_check(type, values)
        result: list[bool] = []
        for batch in chunks(values, 50):
            data = list_response(
                await self._http.get(
                    "/me/following/contains",
                    params={"type": type, "ids": ",".join(batch)},
                )
            )
            if len(data) != len(batch) or any(
                not isinstance(value, bool) for value in data
            ):
                raise SpotifyResponseError(
                    "Following response must have one boolean per requested ID"
                )
            result.extend(data)
        return result

    async def iter_following(
        self, *, limit: int = 50, **kwargs: Any
    ) -> AsyncIterator[Artist]:
        async for item in iter_cursor_items(
            self.following, limit=limit, numeric=False, **kwargs
        ):
            yield item
