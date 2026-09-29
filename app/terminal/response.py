from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, MutableMapping

from app.services.adb import AdbService
from app.services.timeline import Timeline


@dataclass
class TerminalContext:
    config: MutableMapping[str, Any]
    adb: AdbService
    timeline: Timeline
    session: MutableMapping[str, Any]
    args: list[str] = field(default_factory=list)


@dataclass
class TerminalResponse:
    output: list[dict] = field(default_factory=list)
    state: dict = field(default_factory=dict)

    def add(self, text: str, style: str = "text") -> TerminalResponse:
        self.output.append({"text": text, "style": style})
        return self

    def to_dict(self) -> dict:
        return {"output": self.output, "state": self.state}


def success(text: str) -> TerminalResponse:
    return TerminalResponse().add(text, "success")


def error(text: str) -> TerminalResponse:
    return TerminalResponse().add(text, "error")
