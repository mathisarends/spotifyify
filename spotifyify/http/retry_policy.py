from dataclasses import dataclass
from enum import StrEnum
import math
import random
from spotifyify.validation import integer

_RETRYABLE_SERVER_ERROR_STATUS_CODES = frozenset({500, 502, 503, 504})


def parse_retry_after(value: str | None) -> float | None:
    if value is None:
        return None
    try:
        seconds = float(value)
    except ValueError:
        return None
    return max(0.0, seconds) if math.isfinite(seconds) else None


class HttpMethod(StrEnum):
    GET = "GET"
    POST = "POST"
    PUT = "PUT"
    PATCH = "PATCH"
    DELETE = "DELETE"
    HEAD = "HEAD"
    OPTIONS = "OPTIONS"


_IDEMPOTENT_METHODS = frozenset(
    {
        HttpMethod.GET,
        HttpMethod.PUT,
        HttpMethod.DELETE,
        HttpMethod.HEAD,
        HttpMethod.OPTIONS,
    }
)


@dataclass(frozen=True, slots=True)
class RetryDecision:
    retry_number: int
    max_retries: int
    delay_seconds: float


class RetryPolicy:
    def __init__(
        self,
        max_retries: int = 3,
        backoff_seconds: float = 1.0,
        *,
        max_backoff_seconds: float = 30.0,
        max_wait_seconds: float = 60.0,
        jitter: float = 0.0,
    ) -> None:
        integer("max_retries", max_retries)
        if not math.isfinite(backoff_seconds) or backoff_seconds < 0:
            raise ValueError("backoff_seconds must be greater than or equal to 0")
        self.max_retries = max_retries
        self.backoff_seconds = backoff_seconds
        if any(
            not math.isfinite(value) or value < 0
            for value in (max_backoff_seconds, max_wait_seconds, jitter)
        ):
            raise ValueError("Retry limits and jitter must be finite and nonnegative")
        self.max_backoff_seconds = max_backoff_seconds
        self.max_wait_seconds = max_wait_seconds
        self.jitter = jitter

    def should_retry(
        self, method: HttpMethod, status_code: int, *, retry_safe: bool | None = None
    ) -> bool:
        if status_code == 429:
            return True
        return (
            method in _IDEMPOTENT_METHODS if retry_safe is None else retry_safe
        ) and status_code in _RETRYABLE_SERVER_ERROR_STATUS_CODES

    def next_retry(
        self,
        *,
        method: HttpMethod,
        status_code: int,
        retries_used: int,
        retry_after: str | None = None,
        retry_safe: bool | None = None,
    ) -> RetryDecision | None:
        if retries_used >= self.max_retries:
            return None
        if not self.should_retry(method, status_code, retry_safe=retry_safe):
            return None

        delay = self.retry_delay(retries_used, retry_after=retry_after)
        if delay > self.max_wait_seconds:
            return None

        return RetryDecision(
            retry_number=retries_used + 1,
            max_retries=self.max_retries,
            delay_seconds=delay,
        )

    def retry_delay(self, attempt: int, *, retry_after: str | None = None) -> float:
        if (seconds := parse_retry_after(retry_after)) is not None:
            return seconds
        base = min(
            self.max_backoff_seconds, self.backoff_seconds * (2 ** min(attempt, 30))
        )
        return min(
            self.max_backoff_seconds, base + random.uniform(0, base * self.jitter)
        )
