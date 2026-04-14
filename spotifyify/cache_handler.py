import abc
import json
from pathlib import Path
from typing import Any


class CacheHandler(abc.ABC):
    @abc.abstractmethod
    def get_cached_token(self) -> dict[str, Any] | None:
        raise NotImplementedError

    @abc.abstractmethod
    def save_token_to_cache(self, token_info: dict[str, Any]) -> None:
        raise NotImplementedError


class MemoryCacheHandler(CacheHandler):
    def __init__(self, token_info: dict[str, Any] | None = None) -> None:
        self._token_info = token_info

    def get_cached_token(self) -> dict[str, Any] | None:
        return self._token_info

    def save_token_to_cache(self, token_info: dict[str, Any]) -> None:
        self._token_info = token_info


class CacheFileHandler(CacheHandler):
    def __init__(self, cache_path: str | Path = ".cache") -> None:
        self.cache_path = Path(cache_path)

    def get_cached_token(self) -> dict[str, Any] | None:
        if not self.cache_path.exists():
            return None
        try:
            return json.loads(self.cache_path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            return None

    def save_token_to_cache(self, token_info: dict[str, Any]) -> None:
        self.cache_path.parent.mkdir(parents=True, exist_ok=True)
        self.cache_path.write_text(json.dumps(token_info), encoding="utf-8")
