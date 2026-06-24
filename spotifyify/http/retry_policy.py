from dataclasses import dataclass
from enum import StrEnum

_RETRYABLE_SERVER_ERROR_STATUS_CODES = frozenset({500, 502, 503, 504})


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
    ) -> None:
        if max_retries < 0:
            raise ValueError("max_retries must be greater than or equal to 0")
        if backoff_seconds < 0:
            raise ValueError("backoff_seconds must be greater than or equal to 0")
        self.max_retries = max_retries
        self.backoff_seconds = backoff_seconds

    def should_retry(self, method: HttpMethod, status_code: int) -> bool:
        if status_code == 429:
            return True
        return (
            method in _IDEMPOTENT_METHODS
            and status_code in _RETRYABLE_SERVER_ERROR_STATUS_CODES
        )

    def next_retry(
        self,
        *,
        method: HttpMethod,
        status_code: int,
        retries_used: int,
        retry_after: str | None = None,
    ) -> RetryDecision | None:
        if retries_used >= self.max_retries:
            return None
        if not self.should_retry(method, status_code):
            return None

        return RetryDecision(
            retry_number=retries_used + 1,
            max_retries=self.max_retries,
            delay_seconds=self.retry_delay(retries_used, retry_after=retry_after),
        )

    def retry_delay(self, attempt: int, *, retry_after: str | None = None) -> float:
        if retry_after is not None:
            try:
                return max(0.0, float(retry_after))
            except ValueError:
                pass
        return self.backoff_seconds * (2**attempt)
