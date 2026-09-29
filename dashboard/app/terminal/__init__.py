from __future__ import annotations

import shlex

from app.services.adb import AdbError
from app.terminal import messages
from app.terminal.commands import COMMANDS
from app.terminal.response import TerminalContext, TerminalResponse, error


def run_command(raw_command: str, context: TerminalContext) -> TerminalResponse:
    try:
        parts = shlex.split(raw_command)
    except ValueError:
        return error(messages.INVALID_SYNTAX)
    if not parts:
        return TerminalResponse()
    name, args = _split_command(parts)
    command = COMMANDS.get(name)
    if command is None:
        return error(messages.UNKNOWN_COMMAND.format(name=name))
    if len(args) != command.arg_count:
        return error(messages.USAGE.format(usage=command.usage))
    context.args = args
    try:
        return command.handler(context)
    except AdbError as failure:
        return error(messages.ADB_ERRORS.get(failure.code, messages.ADB_ERRORS["command_failed"]))


def _split_command(parts: list[str]) -> tuple[str, list[str]]:
    if parts[0] == "map" and len(parts) > 1:
        return f"map {parts[1]}", parts[2:]
    return parts[0], parts[1:]
