from __future__ import annotations

import secrets
from datetime import datetime
from io import BytesIO
from zoneinfo import ZoneInfo

from PIL import Image, UnidentifiedImageError
from pillow_heif import register_heif_opener


register_heif_opener()

FORMAT_EXTENSIONS = {"JPEG": ".jpg", "MPO": ".jpg", "PNG": ".png", "WEBP": ".webp", "HEIF": ".heic"}

TIMEZONE = ZoneInfo("America/Sao_Paulo")


class InvalidImageError(Exception):
    pass


def detect_extension(data: bytes) -> str:
    try:
        with Image.open(BytesIO(data)) as image:
            image_format = image.format
            image.verify()
    except (UnidentifiedImageError, OSError, SyntaxError, ValueError, Image.DecompressionBombError) as error:
        raise InvalidImageError from error
    if image_format not in FORMAT_EXTENSIONS:
        raise InvalidImageError
    return FORMAT_EXTENSIONS[image_format]


def build_upload_name(extension: str) -> str:
    return f"upload_{datetime.now(TIMEZONE):%Y%m%d_%H%M%S}_{secrets.token_hex(2)}{extension}"
