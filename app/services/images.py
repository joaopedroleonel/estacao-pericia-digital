from __future__ import annotations

import hashlib
import secrets
from datetime import datetime
from io import BytesIO
from pathlib import Path
from typing import Iterable

from PIL import Image, ImageOps, UnidentifiedImageError

from app.utils import is_safe_filename


try:
    from pillow_heif import register_heif_opener
except ImportError:
    pass
else:
    register_heif_opener()


FORMAT_EXTENSIONS = {"JPEG": ".jpg", "MPO": ".jpg", "PNG": ".png", "WEBP": ".webp", "HEIF": ".heic"}

HASH_CHUNK_SIZE = 1024 * 1024


class InvalidImageError(Exception):
    pass


def validate_upload(data: bytes) -> str:
    try:
        with Image.open(BytesIO(data)) as image:
            image_format = image.format
            image.verify()
    except (UnidentifiedImageError, OSError, SyntaxError, ValueError) as error:
        raise InvalidImageError from error
    if image_format not in FORMAT_EXTENSIONS:
        raise InvalidImageError
    return FORMAT_EXTENSIONS[image_format]


def save_upload(data: bytes, uploads_dir: Path) -> Path:
    extension = validate_upload(data)
    path = uploads_dir / f"upload_{datetime.now():%Y%m%d_%H%M%S}_{secrets.token_hex(2)}{extension}"
    path.write_bytes(data)
    return path


def build_preview(source: Path, previews_dir: Path, max_size: int) -> Path:
    target = previews_dir / f"{source.parent.name}_{source.stem}.jpg"
    if target.exists() and target.stat().st_mtime >= source.stat().st_mtime:
        return target
    with Image.open(source) as image:
        preview = ImageOps.exif_transpose(image)
        preview.thumbnail((max_size, max_size))
        preview.convert("RGB").save(target, "JPEG", quality=85)
    return target


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as file:
        for chunk in iter(lambda: file.read(HASH_CHUNK_SIZE), b""):
            digest.update(chunk)
    return digest.hexdigest()


def find_image(name: str, folders: Iterable[Path]) -> Path | None:
    if not is_safe_filename(name):
        return None
    for folder in folders:
        path = folder / name
        if path.is_file():
            return path
    return None


def list_images(folder: Path) -> list[Path]:
    images = [path for path in folder.iterdir() if path.is_file() and is_safe_filename(path.name)]
    return sorted(images, key=lambda path: path.stat().st_mtime, reverse=True)
