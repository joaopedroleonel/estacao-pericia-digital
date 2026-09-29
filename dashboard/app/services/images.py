from __future__ import annotations

import hashlib
from pathlib import Path
from typing import Iterable

from PIL import Image, ImageOps

from app.utils import is_safe_filename


try:
    from pillow_heif import register_heif_opener
except ImportError:
    pass
else:
    register_heif_opener()


HASH_CHUNK_SIZE = 1024 * 1024


def preview_path(source: Path, previews_dir: Path) -> Path:
    return previews_dir / f"{source.parent.name}_{source.stem}.jpg"


def build_preview(source: Path, previews_dir: Path, max_size: int) -> Path:
    target = preview_path(source, previews_dir)
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


def delete_images(folder: Path, previews_dir: Path) -> int:
    images = list_images(folder)
    for path in images:
        preview_path(path, previews_dir).unlink(missing_ok=True)
        path.unlink()
    return len(images)


def list_images(folder: Path) -> list[Path]:
    images = [path for path in folder.iterdir() if path.is_file() and is_safe_filename(path.name)]
    return sorted(images, key=lambda path: path.stat().st_mtime, reverse=True)
