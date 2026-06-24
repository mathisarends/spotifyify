import unittest
from unittest.mock import MagicMock

import httpx
from pydantic import BaseModel

from spotifyify.exceptions import SpotifyAPIError, SpotifyRateLimitError
from spotifyify.http.response import parse_response, validate_response_model


class TestParseResponse(unittest.TestCase):
    def _make_response(
        self,
        status_code,
        json_data=None,
        content=b"",
        text="",
        headers=None,
    ):
        response = MagicMock(spec=httpx.Response)
        response.status_code = status_code
        response.content = content
        response.text = text
        response.headers = headers or {}
        if json_data is not None:
            response.json.return_value = json_data
            response.content = b'{"data": true}'
        else:
            response.json.side_effect = ValueError("No JSON")
        return response

    def test_204_returns_none(self):
        self.assertIsNone(parse_response(self._make_response(204)))

    def test_empty_content_returns_none(self):
        self.assertIsNone(parse_response(self._make_response(200)))

    def test_successful_json_is_returned(self):
        self.assertEqual(
            parse_response(self._make_response(200, json_data={"tracks": []})),
            {"tracks": []},
        )

    def test_error_object_raises_api_error(self):
        response = self._make_response(
            400,
            json_data={"error": {"message": "bad request"}},
        )

        with self.assertLogs("spotifyify.http.response", level="WARNING") as logs:
            with self.assertRaises(SpotifyAPIError) as ctx:
                parse_response(response)

        self.assertEqual(ctx.exception.status_code, 400)
        self.assertEqual(ctx.exception.message, "bad request")
        self.assertIn("status_code=400", logs.output[0])

    def test_plain_error_text_raises_api_error(self):
        response = self._make_response(400, text="server error")

        with self.assertRaises(SpotifyAPIError) as ctx:
            parse_response(response)

        self.assertEqual(ctx.exception.message, "server error")

    def test_non_dict_error_raises_api_error(self):
        response = self._make_response(400, json_data={"error": "simple string"})

        with self.assertRaises(SpotifyAPIError) as ctx:
            parse_response(response)

        self.assertEqual(ctx.exception.message, "simple string")

    def test_rate_limit_error_exposes_retry_after_details(self):
        response = self._make_response(
            429,
            json_data={"error": {"message": "rate limited"}},
            headers={"Retry-After": "2.5"},
        )

        with self.assertRaises(SpotifyRateLimitError) as ctx:
            parse_response(response)

        self.assertEqual(ctx.exception.status_code, 429)
        self.assertEqual(ctx.exception.message, "rate limited")
        self.assertEqual(ctx.exception.retry_after, 2.5)
        self.assertIsNotNone(ctx.exception.retry_at)

    def test_rate_limit_error_allows_missing_retry_after(self):
        response = self._make_response(
            429,
            json_data={"error": {"message": "rate limited"}},
        )

        with self.assertRaises(SpotifyRateLimitError) as ctx:
            parse_response(response)

        self.assertIsNone(ctx.exception.retry_after)
        self.assertIsNone(ctx.exception.retry_at)


class TestValidateResponseModel(unittest.TestCase):
    class ResponseModel(BaseModel):
        name: str

    def test_none_model_returns_parsed_response(self):
        parsed = {"name": "test"}
        self.assertIs(validate_response_model(parsed, None), parsed)

    def test_none_response_returns_none(self):
        self.assertIsNone(validate_response_model(None, self.ResponseModel))

    def test_dict_is_validated(self):
        result = validate_response_model({"name": "test"}, self.ResponseModel)
        self.assertEqual(result, self.ResponseModel(name="test"))

    def test_list_raises_api_error_for_object_model(self):
        with self.assertRaises(SpotifyAPIError):
            validate_response_model([], self.ResponseModel)
