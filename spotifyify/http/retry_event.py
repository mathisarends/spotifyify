from collections.abc import Awaitable, Callable
from dataclasses import dataclass
from datetime import datetime

import httpx

from spotifyify.http.retry_policy import HttpMethod


@dataclass(frozen=True, slots=True)
class RetryEvent:
    method: HttpMethod
    path: str
    response: httpx.Response
    retry_number: int
    max_retries: int
    retry_in_seconds: float
    retry_at: datetime

    @property
    def status_code(self) -> int:
        return self.response.status_code

    @property
    def retry_after(self) -> float:
        return self.retry_in_seconds


type OnRetryHook = Callable[[RetryEvent], Awaitable[None] | None]
