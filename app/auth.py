from __future__ import annotations

import hmac
import math
import time
from functools import wraps
from typing import Callable

from flask import current_app, jsonify, redirect, request, session, url_for


class LoginLimiter:
    def __init__(self, max_attempts: int, lock_seconds: int) -> None:
        self.max_attempts = max_attempts
        self.lock_seconds = lock_seconds
        self._failures: dict[str, int] = {}
        self._locked_until: dict[str, float] = {}

    def remaining_lock_seconds(self, client: str) -> int:
        remaining = self._locked_until.get(client, 0) - time.monotonic()
        return max(0, math.ceil(remaining))

    def register_failure(self, client: str) -> None:
        failures = self._failures.get(client, 0) + 1
        if failures >= self.max_attempts:
            self._locked_until[client] = time.monotonic() + self.lock_seconds
            failures = 0
        self._failures[client] = failures

    def reset(self, client: str) -> None:
        self._failures.pop(client, None)
        self._locked_until.pop(client, None)


def is_valid_access_code(code: str) -> bool:
    return _matches(code, current_app.config["ACCESS_CODE"])


def login_required(view: Callable) -> Callable:
    @wraps(view)
    def wrapper(*args, **kwargs):
        if session.get("authenticated"):
            return view(*args, **kwargs)
        if request.path.startswith("/api/"):
            return jsonify(error="unauthorized"), 401
        return redirect(url_for("auth.login_page"))

    return wrapper


def _matches(received: str, expected: str) -> bool:
    return hmac.compare_digest(received.encode(), expected.encode())
