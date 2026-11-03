import abc
import hashlib
import json
import logging
import os
import tempfile
from copy import deepcopy
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

    def delete_cached_token(self) -> None:
        """Invalidate a grant. Custom handlers may override physical deletion."""
        self.save_token_to_cache({})


class MemoryCacheHandler(CacheHandler):
    def __init__(self, token_info: dict[str, Any] | None = None) -> None:
        self._token_info = deepcopy(token_info)

    def get_cached_token(self) -> dict[str, Any] | None:
        logger.debug("Reading token from memory cache")
        return deepcopy(self._token_info)

    def save_token_to_cache(self, token_info: dict[str, Any]) -> None:
        logger.debug("Saving token to memory cache")
        self._token_info = deepcopy(token_info)

    def delete_cached_token(self) -> None:
        self._token_info = None


def default_cache_path(client_id: str | None = None, profile: str = "default") -> Path:
    """Keep separate grants per app and caller-selected account profile."""
    if os.name == "nt":
        root = Path(os.environ.get("LOCALAPPDATA", Path.home() / "AppData" / "Local"))
    else:
        root = Path(os.environ.get("XDG_CACHE_HOME", Path.home() / ".cache"))
    key = hashlib.sha256(f"{client_id or 'external'}\0{profile}".encode()).hexdigest()[
        :32
    ]
    return root / "spotifyify" / "tokens" / f"{key}.json"


class CacheFileHandler(CacheHandler):
    def __init__(
        self,
        cache_path: str | Path | None = None,
        *,
        client_id: str | None = None,
        profile: str = "default",
    ) -> None:
        self.cache_path = (
            Path(cache_path)
            if cache_path is not None
            else default_cache_path(client_id, profile)
        )

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
        if (
            not isinstance(token_info, dict)
            or not isinstance(token_info.get("access_token"), str)
            or not token_info["access_token"]
        ):
            logger.warning("Ignoring invalid token cache: path=%s", self.cache_path)
            return None
        logger.debug("Read token from cache file: path=%s", self.cache_path)
        return token_info

    def save_token_to_cache(self, token_info: dict[str, Any]) -> None:
        temporary_path: Path | None = None
        try:
            parent_existed = self.cache_path.parent.exists()
            self.cache_path.parent.mkdir(parents=True, exist_ok=True)
            if os.name != "nt" and not parent_existed:
                self.cache_path.parent.chmod(0o700)
            descriptor, name = tempfile.mkstemp(
                prefix=".token-", dir=self.cache_path.parent
            )
            temporary_path = Path(name)
            with os.fdopen(descriptor, "w", encoding="utf-8") as stream:
                json.dump(token_info, stream)
                stream.flush()
                os.fsync(stream.fileno())
            # mkstemp creates owner-only files on POSIX. On Windows the file
            # inherits the ACL of the user's application data directory.
            os.replace(temporary_path, self.cache_path)
        except OSError:
            logger.exception(
                "Unable to save token cache file: path=%s",
                self.cache_path,
            )
            raise
        finally:
            if temporary_path is not None:
                temporary_path.unlink(missing_ok=True)
        logger.debug("Saved token to cache file: path=%s", self.cache_path)

    def delete_cached_token(self) -> None:
        self.cache_path.unlink(missing_ok=True)
