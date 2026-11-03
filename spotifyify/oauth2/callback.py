"""Explicit loopback authorization flow used by the CLI."""

import asyncio
from collections.abc import Callable
from ipaddress import ip_address
from urllib.parse import parse_qs, urlparse

from spotifyify.exceptions import SpotifyAuthError


def parse_callback_url(value: str, state: str) -> str:
    query = parse_qs(urlparse(value.strip()).query)
    if query.get("state", [None])[0] != state:
        raise SpotifyAuthError("State mismatch during OAuth callback")
    if error := query.get("error", [None])[0]:
        raise SpotifyAuthError(f"Spotify authorization failed: {error}")
    code = query.get("code", [None])[0]
    if not code:
        raise SpotifyAuthError("No authorization code received")
    return code


async def capture_local_code(
    redirect_uri: str,
    *,
    state: str,
    on_ready: Callable[[], None],
    timeout: float = 180.0,
) -> str:
    parsed = urlparse(redirect_uri)
    try:
        loopback = ip_address(parsed.hostname or "").is_loopback
    except ValueError:
        loopback = False
    if parsed.scheme != "http" or not loopback:
        raise SpotifyAuthError(
            "Automatic login needs an HTTP loopback redirect URI; use --manual for other redirects"
        )
    future: asyncio.Future[str] = asyncio.get_running_loop().create_future()
    handlers: set[asyncio.Task] = set()

    async def handle(
        reader: asyncio.StreamReader, writer: asyncio.StreamWriter
    ) -> None:
        task = asyncio.current_task()
        if task is not None:
            handlers.add(task)
        status, body = "400 Bad Request", "Invalid callback."
        try:
            async with asyncio.timeout(5):
                parts = (
                    (await reader.readline()).decode("utf-8", errors="replace").split()
                )
                total = 0
                while line := await reader.readline():
                    total += len(line)
                    if total > 16384:
                        return
                    if line in {b"\r\n", b"\n"}:
                        break
                if (
                    len(parts) >= 2
                    and parts[0] == "GET"
                    and urlparse(parts[1]).path == (parsed.path or "/")
                ):
                    try:
                        code = parse_callback_url(parts[1], state)
                    except SpotifyAuthError as exc:
                        body = str(exc)
                        # Unrelated local requests must not cancel a valid login.
                        query = parse_qs(urlparse(parts[1]).query)
                        if query.get("state", [None])[0] == state and not future.done():
                            future.set_exception(exc)
                    else:
                        status, body = (
                            "200 OK",
                            "Authorization completed. You can close this window.",
                        )
                        if not future.done():
                            future.set_result(code)
                payload = body.encode("utf-8")
                writer.write(
                    (
                        f"HTTP/1.1 {status}\r\nContent-Type: text/plain; charset=utf-8\r\nContent-Length: {len(payload)}\r\nConnection: close\r\n\r\n"
                    ).encode()
                    + payload
                )
                await writer.drain()
        except (TimeoutError, ConnectionError, ValueError):
            pass
        finally:
            writer.close()
            try:
                await writer.wait_closed()
            except ConnectionError:
                pass
            if task is not None:
                handlers.discard(task)

    try:
        server = await asyncio.start_server(
            handle, host=parsed.hostname, port=parsed.port or 80
        )
    except OSError as exc:
        raise SpotifyAuthError(
            "Unable to bind the OAuth callback port; close the other listener or use --manual"
        ) from exc
    try:
        async with server:
            # The listener is ready before the browser can redirect back.
            await asyncio.to_thread(on_ready)
            return await asyncio.wait_for(future, timeout)
    except TimeoutError as exc:
        raise SpotifyAuthError("Timed out waiting for Spotify authorization") from exc
    finally:
        for task in tuple(handlers):
            task.cancel()
        await asyncio.gather(*handlers, return_exceptions=True)
