import asyncio
import inspect
import logging
from typing import Any
from datetime import UTC, datetime, timedelta

import httpx

from spotifyify.http.retry_context import current_retry_hook
from spotifyify.http.retry_event import RetryEvent
from spotifyify.http.retry_policy import HttpMethod, RetryPolicy
from spotifyify.http.serialization import SerializedJsonPayload

logger = logging.getLogger(__name__)


class HttpTransport:
    def __init__(
        self,
        *,
        base_url: str,
        timeout: float,
        retry_policy: RetryPolicy,
    ) -> None:
        self._base_url = base_url
        self._timeout = timeout
        self._retry_policy = retry_policy
        self._client: httpx.AsyncClient | None = None

    async def open(self) -> None:
        if self._client is None:
            logger.debug("Opening HTTP transport: base_url=%s", self._base_url)
            self._client = httpx.AsyncClient(
                base_url=self._base_url,
                timeout=self._timeout,
            )

    async def close(self) -> None:
        if self._client is None:
            return
        logger.debug("Closing HTTP transport: base_url=%s", self._base_url)
        await self._client.aclose()
        self._client = None

    async def request(
        self,
        method: HttpMethod,
        path: str,
        *,
        headers: dict[str, str],
        params: dict[str, Any] | None,
        json: SerializedJsonPayload,
        content: str | bytes | None,
    ) -> httpx.Response:
        await self.open()
        if self._client is None:
            raise RuntimeError("HTTP client was not initialized")

        for attempt in range(self._retry_policy.max_retries + 1):
            logger.debug(
                "Sending HTTP request: method=%s path=%s attempt=%d/%d",
                method.value,
                path,
                attempt + 1,
                self._retry_policy.max_retries + 1,
            )
            try:
                response = await self._client.request(
                    method.value,
                    path,
                    headers=headers,
                    params=params,
                    json=json,
                    content=content,
                )
            except httpx.HTTPError:
                logger.exception(
                    "HTTP request failed: method=%s path=%s",
                    method.value,
                    path,
                )
                raise
            logger.debug(
                "Received HTTP response: method=%s path=%s status_code=%d",
                method.value,
                path,
                response.status_code,
            )
            if attempt == self._retry_policy.max_retries or not (
                self._retry_policy.should_retry(method, response.status_code)
            ):
                return response
            retry_delay = self._retry_policy.retry_delay(
                attempt,
                retry_after=response.headers.get("Retry-After"),
            )
            retry_event = RetryEvent(
                method=method,
                path=path,
                response=response,
                retry_number=attempt + 1,
                max_retries=self._retry_policy.max_retries,
                retry_in_seconds=retry_delay,
                retry_at=datetime.now(UTC) + timedelta(seconds=retry_delay),
            )
            logger.warning(
                "Retrying HTTP request: method=%s path=%s status_code=%d "
                "retry_in_seconds=%s retry=%d/%d",
                method.value,
                path,
                response.status_code,
                retry_delay,
                retry_event.retry_number,
                retry_event.max_retries,
            )
            if (hook := current_retry_hook.get()) is not None:
                result = hook(retry_event)
                if inspect.isawaitable(result):
                    await result
            await asyncio.sleep(retry_delay)

        raise RuntimeError("unreachable")
