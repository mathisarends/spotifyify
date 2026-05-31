import abc
import json
import logging
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)


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
        logger.debug("Reading token from memory cache")
        return self._token_info

    def save_token_to_cache(self, token_info: dict[str, Any]) -> None:
        logger.debug("Saving token to memory cache")
        self._token_info = token_info


class CacheFileHandler(CacheHandler):
    def __init__(self, cache_path: str | Path = ".cache") -> None:
        self.cache_path = Path(cache_path)

    def get_cached_token(self) -> dict[str, Any] | None:
        if not self.cache_path.exists():
            logger.debug("Token cache file does not exist: path=%s", self.cache_path)
            return None
        try:
            token_info = json.loads(self.cache_path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            logger.warning(
                "Unable to read token cache file: path=%s",
                self.cache_path,
                exc_info=True,
            )
            return None
        logger.debug("Read token from cache file: path=%s", self.cache_path)
        return token_info

    def save_token_to_cache(self, token_info: dict[str, Any]) -> None:
        try:
            self.cache_path.parent.mkdir(parents=True, exist_ok=True)
            self.cache_path.write_text(json.dumps(token_info), encoding="utf-8")
        except OSError:
            logger.exception(
                "Unable to save token cache file: path=%s",
                self.cache_path,
            )
            raise
        logger.debug("Saved token to cache file: path=%s", self.cache_path)
