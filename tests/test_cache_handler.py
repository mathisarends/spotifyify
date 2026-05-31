import tempfile
import unittest
from pathlib import Path

from spotifyify.cache_handler import CacheFileHandler, MemoryCacheHandler


class TestMemoryCacheHandler(unittest.TestCase):
    def test_default_returns_none(self):
        handler = MemoryCacheHandler()
        self.assertIsNone(handler.get_cached_token())

    def test_initial_token(self):
        token = {"access_token": "abc"}
        handler = MemoryCacheHandler(token_info=token)
        self.assertEqual(handler.get_cached_token(), token)

    def test_save_and_get(self):
        handler = MemoryCacheHandler()
        token = {"access_token": "xyz", "expires_at": 9999999999}
        handler.save_token_to_cache(token)
        self.assertEqual(handler.get_cached_token(), token)

    def test_overwrite(self):
        handler = MemoryCacheHandler(token_info={"access_token": "old"})
        handler.save_token_to_cache({"access_token": "new"})
        self.assertEqual(handler.get_cached_token()["access_token"], "new")


class TestCacheFileHandler(unittest.TestCase):
    def test_returns_none_when_no_file(self):
        handler = CacheFileHandler(cache_path="/nonexistent/path/.cache")
        self.assertIsNone(handler.get_cached_token())

    def test_save_and_read(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / ".cache-test"
            handler = CacheFileHandler(cache_path=path)
            token = {"access_token": "tok", "expires_at": 12345}
            handler.save_token_to_cache(token)
            result = handler.get_cached_token()
            self.assertEqual(result, token)

    def test_corrupt_json_returns_none(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / ".cache-bad"
            path.write_text("not valid json", encoding="utf-8")
            handler = CacheFileHandler(cache_path=path)
            with self.assertLogs("spotifyify.cache_handler", level="WARNING") as logs:
                self.assertIsNone(handler.get_cached_token())
            self.assertIn("Unable to read token cache file", logs.output[0])
