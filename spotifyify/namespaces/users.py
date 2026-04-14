from spotifyify.client import SpotifyClient
from spotifyify.schemas import CursorPagingSimplifiedArtist, PublicUser, User


class Users:
    def __init__(self, http: SpotifyClient) -> None:
        self._http = http

    async def me(self) -> User:
        data = await self._http.get("/me") or {}
        return User.model_validate(data)

    async def get(self, user_id: str) -> PublicUser:
        data = await self._http.get(f"/users/{user_id}", require_user=False) or {}
        return PublicUser.model_validate(data)

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
        return CursorPagingSimplifiedArtist.model_validate(artists)

    async def follow(self, type: str, ids: list[str]) -> None:
        await self._http.put(
            "/me/following",
            params={"type": type},
            payload={"ids": ids},
        )

    async def unfollow(self, type: str, ids: list[str]) -> None:
        await self._http.delete(
            "/me/following",
            params={"type": type},
            payload={"ids": ids},
        )

    async def check_following(self, type: str, ids: list[str]) -> list[bool]:
        data = await self._http.get(
            "/me/following/contains",
            params={"type": type, "ids": ",".join(ids)},
        )
        return data if isinstance(data, list) else []
