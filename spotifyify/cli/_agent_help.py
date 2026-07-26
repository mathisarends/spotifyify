from __future__ import annotations

from typing import Any

import click

# Options every read command shares. Listing them once keeps the per-command
# lines short enough that the whole tree fits in a system prompt.
GLOBAL_OPTIONS = frozenset(
    {
        "--format",
        "--json",
        "--field",
        "--fields",
        "-f",
        "--sort",
        "--where",
        "--limit",
        "-l",
        "--offset",
        "-o",
        "--market",
        "-m",
        "--scope",
        "-s",
        "--help",
    }
)

PREAMBLE = """\
spotifyify GROUP COMMAND [ARGS] [OPTIONS]

Output contract:
  JSON on stdout, always. --format table for aligned text. Never switches on isatty().
  No ANSI, no pager, no prompts. Errors go to stderr.
  Exit 0 ok, 1 API error, 2 usage, 3 auth, 4 no match.
  Row order is whatever Spotify returned; --sort FIELD is a stable re-sort ('-' reverses).
  Mutations print the state they produced, not "ok".
Global options: --format json|table --json --field F,F --sort F,-F --where PATH=VALUE
                --limit N --offset N --market XX --scope S
IDs, URIs, fields and scopes accept repeated or comma-separated values.
Group names tolerate the singular form (artist -> artists).

Commands (ARG... means variadic):"""


def _is_group(command: Any) -> bool:
    # Typer vendors its own click classes, so isinstance against click is unsafe.
    return hasattr(command, "list_commands")


def _is_argument(param: Any) -> bool:
    return getattr(param, "param_type_name", None) == "argument"


def _argument_names(command: Any) -> list[str]:
    return [
        f"{param.name.upper()}..." if param.nargs == -1 else param.name.upper()
        for param in command.params
        if _is_argument(param)
    ]


def _option_names(command: Any) -> list[str]:
    names = []
    for param in command.params:
        if _is_argument(param):
            continue
        long_opts = [opt for opt in param.opts if opt.startswith("--")]
        if not long_opts:
            continue
        flag = long_opts[0]
        if flag in GLOBAL_OPTIONS:
            continue
        names.append(flag)
    return names


def _signature(name: str, command: Any) -> str:
    parts = [name, *_argument_names(command)]
    options = _option_names(command)
    if options:
        parts.append(f"[{' '.join(options)}]")
    return " ".join(parts)


def _group_line(name: str, group: Any, ctx: click.Context) -> str:
    signatures = []
    for command_name in group.list_commands(ctx):
        command = group.get_command(ctx, command_name)
        if command is None or command.hidden:
            continue
        signatures.append(_signature(command_name, command))
    return f"{name}: " + " | ".join(signatures)


def agent_help(root: Any, program_name: str = "spotifyify") -> str:
    """Dump the whole command tree in one shot, straight from the real tree."""
    lines = [PREAMBLE]
    with click.Context(root, info_name=program_name) as ctx:
        for name in root.list_commands(ctx):
            command = root.get_command(ctx, name)
            if command is None or command.hidden:
                continue
            if _is_group(command):
                lines.append(_group_line(name, command, ctx))
            else:
                lines.append(_signature(name, command))
    return "\n".join(lines)
