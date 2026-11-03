import asyncio
import secrets
import sys
import webbrowser
from typing import Annotated

import typer

from spotifyify.cache_handler import CacheFileHandler
from spotifyify.cli.core import default_profile, print_json, split_values
from spotifyify.cli.options import async_command
from spotifyify.credentials import SpotifyCredentials
from spotifyify.exceptions import SpotifyAuthError
from spotifyify.oauth2 import SpotifyOAuth
from spotifyify.oauth2.callback import capture_local_code, parse_callback_url

app = typer.Typer(
    help="Explicit user authorization and cached account profiles.",
    no_args_is_help=True,
    rich_markup_mode=None,
)


def _provider() -> SpotifyOAuth:
    credentials = SpotifyCredentials()
    return SpotifyOAuth(
        credentials,
        CacheFileHandler(client_id=credentials.client_id, profile=default_profile()),
    )


@app.command("login")
@async_command
async def login(
    scope: Annotated[
        list[str] | None,
        typer.Option("--scope", help="OAuth scope; repeat or separate with commas."),
    ] = None,
    manual: Annotated[
        bool,
        typer.Option(
            "--manual",
            help="Explicitly paste the redirect URL instead of starting a callback listener.",
        ),
    ] = False,
    browser: Annotated[bool, typer.Option("--browser/--no-browser")] = True,
    timeout: Annotated[float, typer.Option("--timeout", min=1, max=600)] = 180,
) -> None:
    oauth = _provider()
    try:
        state = secrets.token_urlsafe(24)
        scopes = split_values(scope)
        current = oauth.token_info
        if current and current.auth_type == "user" and current.scope:
            scopes = sorted(set(scopes) | set(current.scope.split()))
        url = oauth.authorization_url(state=state, scope=scopes)

        def announce() -> None:
            print(f"Open this URL to authorize Spotify access:\n{url}", file=sys.stderr)
            if browser:
                try:
                    webbrowser.open(url)
                except OSError:
                    print(
                        "Unable to open a browser; open the URL above manually.",
                        file=sys.stderr,
                    )

        if manual:
            announce()
            print(
                "Paste the full redirect URL:\n> ", end="", file=sys.stderr, flush=True
            )
            try:
                code = parse_callback_url(await asyncio.to_thread(input), state)
            except EOFError as exc:
                raise SpotifyAuthError("No redirect URL received") from exc
        else:
            code = await capture_local_code(
                oauth.credentials.redirect_uri or "",
                state=state,
                on_ready=announce,
                timeout=timeout,
            )
        token = await oauth.exchange_code(code, scope=scopes)
        print_json(
            [
                {
                    "authenticated": True,
                    "profile": default_profile(),
                    "scope": token.scope,
                }
            ]
        )
    finally:
        await oauth.close()


@app.command("logout")
@async_command
async def logout() -> None:
    """Remove the selected profile's cached grant. Environment tokens are external."""
    credentials = SpotifyCredentials()
    try:
        CacheFileHandler(
            client_id=credentials.client_id, profile=default_profile()
        ).delete_cached_token()
    except OSError as exc:
        raise SpotifyAuthError("Unable to remove the selected token cache") from exc
    print_json([{"profile": default_profile(), "cache_removed": True}])


@app.command("status")
@async_command
async def status() -> None:
    """Inspect local authorization without refreshing or revealing tokens."""
    oauth = _provider()
    try:
        token = oauth.token_info
        print_json(
            [
                {
                    "profile": default_profile(),
                    "authenticated": bool(
                        token and token.auth_type == "user" and not token.expired
                    ),
                    "expires_at": token.expires_at if token else None,
                    "scope": token.scope if token else None,
                }
            ]
        )
    finally:
        await oauth.close()
