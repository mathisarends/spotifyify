from collections.abc import Iterable
from spotifyify.batching import chunks
from spotifyify.config import ApiMode
from spotifyify.exceptions import SpotifyResponseError
from spotifyify.http.response import list_response
from spotifyify.namespaces.base import Resource
from spotifyify.utils import coalesce_items
from spotifyify.http.response import validate_model
from spotifyify.schemas import CursorPagingSimplifiedArtist, PublicUser, User


class Users(Resource):
    async def me(self) -> User:
        data = await self._http.get("/me") or {}
        return validate_model(User, data)

    async def get(self, user_id: str) -> PublicUser:
        self._require_extended("Other user profiles")
        data = await self._http.get(f"/users/{user_id}", require_user=False) or {}
        return validate_model(PublicUser, data)

    async def following(
        self,
        *,
        type: str = "artist",
        limit: int = 20,
        after: str | None = None,
    ) -> CursorPagingSimplifiedArtist:
        params: dict[str, str | int] = {"type": type, "limit": limit}
        if after:
            params["after"] = after
        data = await self._http.get("/me/following", params=params) or {}
        artists = data.get("artists", {}) if isinstance(data, dict) else {}
        return validate_model(CursorPagingSimplifiedArtist, artists)

    async def follow(self, type: str, ids: Iterable[str]) -> None:
        if type not in {"artist", "user"}:
            raise ValueError("type must be artist or user")
        values = coalesce_items(ids)
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
        values = coalesce_items(ids)
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
        values = coalesce_items(ids)
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
