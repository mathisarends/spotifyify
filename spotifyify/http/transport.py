from typing import Any

import asyncio
import httpx

from spotifyify.http.retry_policy import HttpMethod, RetryPolicy
from spotifyify.http.serialization import SerializedJsonPayload


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
            self._client = httpx.AsyncClient(
                base_url=self._base_url,
                timeout=self._timeout,
            )

    async def close(self) -> None:
        if self._client is None:
            return
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
            response = await self._client.request(
                method.value,
                path,
                headers=headers,
                params=params,
                json=json,
                content=content,
            )
            if attempt == self._retry_policy.max_retries or not (
                self._retry_policy.should_retry(method, response.status_code)
            ):
                return response
            await asyncio.sleep(
                self._retry_policy.retry_delay(
                    attempt,
                    retry_after=response.headers.get("Retry-After"),
                )
            )

        raise RuntimeError("unreachable")
