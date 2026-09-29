from __future__ import annotations

import math
import re
from pathlib import Path
from typing import Iterable


ALLOWED_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp", ".heic"}

SAFE_FILENAME = re.compile(r"[A-Za-z0-9_.-]{1,128}")


def is_safe_filename(name: str) -> bool:
    return (
        bool(SAFE_FILENAME.fullmatch(name))
        and not name.startswith(".")
        and Path(name).suffix.lower() in ALLOWED_EXTENSIONS
    )


def parse_degree_pair(text: object) -> tuple[float, float] | None:
    if not isinstance(text, str):
        return None
    try:
        latitude, longitude = (float(part.replace("°", "").strip()) for part in text.split(","))
    except ValueError:
        return None
    if abs(latitude) > 90 or abs(longitude) > 180:
        return None
    return latitude, longitude


def dms_to_decimal(values: Iterable | None, reference: object) -> float | None:
    try:
        degrees, minutes, seconds = (float(value) for value in values)
    except (TypeError, ValueError):
        return None
    decimal = degrees + minutes / 60 + seconds / 3600
    if math.isnan(decimal):
        return None
    if str(reference).strip().upper() in ("S", "W"):
        decimal = -decimal
    return round(decimal, 6)
