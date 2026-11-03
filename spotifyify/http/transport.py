import asyncio
import inspect
import logging
from datetime import UTC, datetime, timedelta
from typing import Any

import httpx2

from spotifyify.exceptions import SpotifyTransportError
from spotifyify.http.context import RequestContext, default_context
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
        context: RequestContext | None = None,
        transport: httpx2.AsyncBaseTransport | None = None,
    ) -> None:
        self._base_url = base_url
        self._timeout = timeout
        self._retry_policy = retry_policy
        self._client: httpx2.AsyncClient | None = None
        self._context = context if context is not None else default_context
        self._transport = transport
        self._cooldown_until = 0.0

    async def _wait_cooldown(self) -> None:
        while True:
            deadline = self._cooldown_until
            delay = deadline - asyncio.get_running_loop().time()
            if delay > 0:
                await asyncio.sleep(delay)
            if deadline == self._cooldown_until:
                return

    async def open(self) -> None:
        if self._client is None:
            logger.debug("Opening HTTP transport: base_url=%s", self._base_url)
            self._client = httpx2.AsyncClient(
                base_url=self._base_url,
                timeout=self._timeout,
                transport=self._transport,
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
        retry_safe: bool | None = None,
    ) -> httpx2.Response:
        await self.open()
        if self._client is None:
            raise RuntimeError("HTTP client was not initialized")

        retries_used = 0
        while True:
            await self._wait_cooldown()
            logger.debug(
                "Sending HTTP request: method=%s path=%s attempt=%d/%d",
                method.value,
                path,
                retries_used + 1,
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
            except httpx2.HTTPError as exc:
                logger.exception(
                    "HTTP request failed: method=%s path=%s",
                    method.value,
                    path,
                )
                raise SpotifyTransportError(
                    f"HTTP request failed: {method.value} {path} ({type(exc).__name__})"
                ) from exc
            logger.debug(
                "Received HTTP response: method=%s path=%s status_code=%d",
                method.value,
                path,
                response.status_code,
            )
            if response.status_code == 429:
                try:
                    error = response.json().get("error", {})
                except (ValueError, AttributeError):
                    error = {}
                if isinstance(error, dict) and error.get("reason") == "QUOTA_EXCEEDED":
                    return response
            retry = self._retry_policy.next_retry(
                method=method,
                status_code=response.status_code,
                retry_after=response.headers.get("Retry-After"),
                retries_used=retries_used,
                retry_safe=retry_safe,
            )
            if retry is None:
                return response
            if response.status_code == 429:
                self._cooldown_until = max(
                    self._cooldown_until,
                    asyncio.get_running_loop().time() + retry.delay_seconds,
                )
            retry_event = RetryEvent(
                method=method,
                path=path,
                response=response,
                retry_number=retry.retry_number,
                max_retries=retry.max_retries,
                retry_in_seconds=retry.delay_seconds,
                retry_at=datetime.now(UTC) + timedelta(seconds=retry.delay_seconds),
            )
            logger.warning(
                "Retrying HTTP request: method=%s path=%s status_code=%d "
                "retry_in_seconds=%s retry=%d/%d",
                method.value,
                path,
                response.status_code,
                retry.delay_seconds,
                retry_event.retry_number,
                retry_event.max_retries,
            )
            if (hook := self._context.on_retry.get()) is not None:
                result = hook(retry_event)
                if inspect.isawaitable(result):
                    await result
            retries_used += 1
            if response.status_code != 429:
                await asyncio.sleep(retry.delay_seconds)
