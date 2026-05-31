from typing import Protocol


class AccessTokenProvider(Protocol):
    async def get_access_token(
        self,
        require_user: bool,
        scope: str | list[str] | tuple[str, ...] | None = None,
    ) -> str: ...
