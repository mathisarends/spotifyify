"""Common response behavior; unknown server fields remain available to callers."""

from typing import Any, ClassVar

from pydantic import BaseModel, ConfigDict, model_validator


class SpotifyModel(BaseModel):
    model_config = ConfigDict(extra="allow")
    _legacy_aliases: ClassVar[dict[str, str]] = {}

    @model_validator(mode="before")
    @classmethod
    def normalize_legacy_fields(cls, value: Any) -> Any:
        if not isinstance(value, dict) or not cls._legacy_aliases:
            return value
        result = dict(value)
        for old, new in cls._legacy_aliases.items():
            if old in result:
                if new not in result:
                    result[new] = result[old]
                result.pop(old)
        return result
