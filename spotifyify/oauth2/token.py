"""Validated OAuth state, kept separate from environment configuration."""

import time
from typing import Any, Literal

from pydantic import BaseModel, Field, model_validator


class TokenInfo(BaseModel):
    access_token: str = Field(min_length=1, repr=False)
    refresh_token: str | None = Field(default=None, min_length=1, repr=False)
    expires_at: int | None = None
    scope: str | None = None
    auth_type: Literal["user", "client_credentials", "unknown"] = "unknown"

    @model_validator(mode="before")
    @classmethod
    def infer_legacy_token_type(cls, value: Any) -> Any:
        if isinstance(value, dict) and "auth_type" not in value:
            value = dict(value)
            if value.get("refresh_token"):
                value["auth_type"] = "user"
        return value

    @property
    def expired(self) -> bool:
        # Caller-supplied tokens may have an unknown expiry. Spotify validates them.
        return self.expires_at is not None and self.expires_at <= time.time() + 30

    def permits(self, scope: str | None) -> bool:
        # Unknown scopes occur with caller-supplied tokens. Do not invent grants;
        # leave their enforcement to Spotify, just as for request-scoped tokens.
        return (
            not scope
            or self.scope is None
            or set(scope.split()) <= set(self.scope.split())
        )
