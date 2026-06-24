import unittest

from spotifyify.http.retry_policy import HttpMethod, RetryPolicy


class TestRetryPolicy(unittest.TestCase):
    def test_negative_max_retries_raises(self):
        with self.assertRaises(ValueError):
            RetryPolicy(max_retries=-1)

    def test_negative_backoff_raises(self):
        with self.assertRaises(ValueError):
            RetryPolicy(backoff_seconds=-1)

    def test_rate_limit_is_retried_for_post(self):
        self.assertTrue(RetryPolicy().should_retry(HttpMethod.POST, 429))

    def test_server_error_is_retried_for_idempotent_method(self):
        self.assertTrue(RetryPolicy().should_retry(HttpMethod.GET, 503))

    def test_server_error_is_not_retried_for_post(self):
        self.assertFalse(RetryPolicy().should_retry(HttpMethod.POST, 503))

    def test_next_retry_returns_decision(self):
        decision = RetryPolicy(max_retries=2, backoff_seconds=0.25).next_retry(
            method=HttpMethod.GET,
            status_code=503,
            retries_used=1,
        )

        self.assertIsNotNone(decision)
        if decision is None:
            self.fail("expected retry decision")
        self.assertEqual(decision.retry_number, 2)
        self.assertEqual(decision.max_retries, 2)
        self.assertEqual(decision.delay_seconds, 0.5)

    def test_next_retry_returns_none_after_retry_budget_is_exhausted(self):
        decision = RetryPolicy(max_retries=2).next_retry(
            method=HttpMethod.GET,
            status_code=503,
            retries_used=2,
        )

        self.assertIsNone(decision)

    def test_retry_after_is_used(self):
        self.assertEqual(RetryPolicy().retry_delay(2, retry_after="2.5"), 2.5)

    def test_negative_retry_after_is_clamped(self):
        self.assertEqual(RetryPolicy().retry_delay(0, retry_after="-1"), 0.0)

    def test_invalid_retry_after_falls_back_to_exponential_backoff(self):
        policy = RetryPolicy(backoff_seconds=0.25)
        self.assertEqual(policy.retry_delay(2, retry_after="invalid"), 1.0)
