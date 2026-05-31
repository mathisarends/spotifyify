import unittest

from pydantic import BaseModel

from spotifyify.http.serialization import QueryParams, dump_params, dump_payload


class TestDumpParams(unittest.TestCase):
    def test_none_returns_none(self):
        self.assertIsNone(dump_params(None))

    def test_dict_excludes_none(self):
        self.assertEqual(dump_params({"limit": 10, "offset": None}), {"limit": 10})

    def test_pydantic_model_excludes_none(self):
        params = QueryParams(limit=5, offset=None)
        self.assertEqual(dump_params(params), {"limit": 5})


class TestDumpPayload(unittest.TestCase):
    def test_none_returns_none(self):
        self.assertIsNone(dump_payload(None))

    def test_dict_is_returned_unchanged(self):
        payload = {"name": "test"}
        self.assertIs(dump_payload(payload), payload)

    def test_list_is_returned_unchanged(self):
        payload = [1, 2, 3]
        self.assertIs(dump_payload(payload), payload)

    def test_string_is_returned_unchanged(self):
        self.assertIs(dump_payload("hello"), "hello")

    def test_pydantic_model_is_dumped_without_none(self):
        class Payload(BaseModel):
            name: str
            description: str | None = None

        self.assertEqual(dump_payload(Payload(name="test")), {"name": "test"})
