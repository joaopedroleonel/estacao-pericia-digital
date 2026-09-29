from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Callable

from flask import url_for
from PIL import Image

from app.services.cloud_storage import CloudError, sync_uploads
from app.services.images import build_preview, find_image, list_images, sha256_file
from app.services.metadata import ImageMetadata, extract_metadata
from app.terminal import messages
from app.terminal.response import TerminalContext, TerminalResponse, error, success
from app.utils import is_safe_filename


@dataclass(frozen=True)
class Command:
    handler: Callable[[TerminalContext], TerminalResponse]
    usage: str
    arg_count: int = 0


def show_help(context: TerminalContext) -> TerminalResponse:
    response = TerminalResponse()
    for name, command in COMMANDS.items():
        response.add(f"{command.usage:<14}{messages.DESCRIPTIONS[name]}", "muted")
    return response.add(f"{'clear':<14}{messages.DESCRIPTIONS['clear']}", "muted")


def show_device(context: TerminalContext) -> TerminalResponse:
    return TerminalResponse().add(messages.DEVICE_INFO.format(**context.adb.get_device_info()))


def list_photos(context: TerminalContext) -> TerminalResponse:
    names = context.adb.list_camera_photos(context.config["PHOTOS_LIST_LIMIT"])
    if not names:
        return error(messages.NO_DEVICE_PHOTOS)
    return _file_list(names)


def pull_photo(context: TerminalContext) -> TerminalResponse:
    name = context.args[0]
    if not is_safe_filename(name):
        return error(messages.INVALID_FILENAME.format(name=name))
    path = context.adb.pull_photo(name, Path(context.config["EXTRACTED_DIR"]))
    return (
        success(messages.PULLED.format(name=name, size=_format_size(path.stat().st_size)))
        .add(f"{sha256_file(path)}  {name}", "muted")
        .add(messages.OPEN_HINT.format(name=name), "muted")
    )


def list_extracted(context: TerminalContext) -> TerminalResponse:
    names = [path.name for path in list_images(Path(context.config["EXTRACTED_DIR"]))]
    if not names:
        return error(messages.NO_EXTRACTED)
    return _file_list(names)


def list_uploads(context: TerminalContext) -> TerminalResponse:
    response = _sync_uploads(context)
    names = [path.name for path in list_images(Path(context.config["UPLOADS_DIR"]))]
    if not names:
        return response.add(messages.NO_UPLOADS, "error")
    return response.extend(_file_list(names))


def open_latest(context: TerminalContext) -> TerminalResponse:
    response = _sync_uploads(context)
    images = list_images(Path(context.config["UPLOADS_DIR"]))
    if not images:
        return response.add(messages.NO_UPLOADS, "error")
    return response.extend(_open(context, images[0]))


def open_image(context: TerminalContext) -> TerminalResponse:
    name = context.args[0]
    path = find_image(name, _image_folders(context))
    if path is None:
        return error(messages.IMAGE_NOT_FOUND.format(name=name))
    return _open(context, path)


def show_exif(context: TerminalContext) -> TerminalResponse:
    path = _current_image(context)
    if path is None:
        return error(messages.NO_IMAGE_OPEN)
    response = TerminalResponse()
    for label, value in _summary_rows(extract_metadata(path)):
        response.add(f"{label:<12}{value or messages.NOT_AVAILABLE}")
    return response


def show_hash(context: TerminalContext) -> TerminalResponse:
    path = _current_image(context)
    if path is None:
        return error(messages.NO_IMAGE_OPEN)
    return TerminalResponse().add(f"{sha256_file(path)}  {path.name}")


def show_route(context: TerminalContext) -> TerminalResponse:
    if context.timeline.is_empty:
        return error(messages.TIMELINE_EMPTY)
    response = success(messages.MAP_ROUTE)
    response.state["map"] = {"action": "route"}
    return response


def show_photo_location(context: TerminalContext) -> TerminalResponse:
    path = _current_image(context)
    if path is None:
        return error(messages.NO_IMAGE_OPEN)
    metadata = extract_metadata(path)
    if not metadata.has_gps:
        return error(messages.NO_GPS)
    response = success(messages.MAP_PHOTO.format(lat=metadata.latitude, lng=metadata.longitude))
    response.state["map"] = _photo_map_state(metadata)
    return response


COMMANDS = {
    "help": Command(show_help, "help"),
    "device": Command(show_device, "device"),
    "photos": Command(list_photos, "photos"),
    "pull": Command(pull_photo, "pull <file>", 1),
    "extracted": Command(list_extracted, "extracted"),
    "uploads": Command(list_uploads, "uploads"),
    "latest": Command(open_latest, "latest"),
    "open": Command(open_image, "open <file>", 1),
    "exif": Command(show_exif, "exif"),
    "hash": Command(show_hash, "hash"),
    "map route": Command(show_route, "map route"),
    "map photo": Command(show_photo_location, "map photo"),
}


def _open(context: TerminalContext, path: Path) -> TerminalResponse:
    try:
        metadata = extract_metadata(path)
        preview = build_preview(path, Path(context.config["PREVIEWS_DIR"]), context.config["PREVIEW_MAX_SIZE"])
    except (OSError, ValueError, Image.DecompressionBombError):
        return error(messages.IMAGE_UNREADABLE)
    context.session["current_image"] = path.name
    response = success(messages.IMAGE_LOADED_WITH_GPS if metadata.has_gps else messages.IMAGE_LOADED_WITHOUT_GPS)
    response.state["image"] = {
        "name": path.name,
        "previewUrl": url_for("api.image_preview", name=preview.name),
        "summary": metadata.summary(),
        "tags": metadata.tags,
    }
    if metadata.has_gps:
        response.state["map"] = _photo_map_state(metadata)
    return response


def _sync_uploads(context: TerminalContext) -> TerminalResponse:
    response = TerminalResponse()
    if context.cloud is None:
        return response
    try:
        downloaded = sync_uploads(context.cloud, Path(context.config["UPLOADS_DIR"]))
    except CloudError:
        return response.add(messages.CLOUD_SYNC_FAILED, "error")
    if downloaded:
        response.add(messages.CLOUD_SYNCED.format(count=downloaded), "success")
    return response


def _current_image(context: TerminalContext) -> Path | None:
    name = context.session.get("current_image")
    return find_image(name, _image_folders(context)) if name else None


def _image_folders(context: TerminalContext) -> list[Path]:
    return [Path(context.config["UPLOADS_DIR"]), Path(context.config["EXTRACTED_DIR"])]


def _photo_map_state(metadata: ImageMetadata) -> dict:
    return {"action": "photo", "lat": metadata.latitude, "lng": metadata.longitude}


def _summary_rows(metadata: ImageMetadata) -> list[tuple[str, str | None]]:
    labels = messages.SUMMARY_LABELS
    return [
        (labels["make"], metadata.make),
        (labels["model"], metadata.model),
        (labels["takenAt"], metadata.taken_at.strftime(messages.DATE_FORMAT) if metadata.taken_at else None),
        (labels["gps"], f"{metadata.latitude}, {metadata.longitude}" if metadata.has_gps else None),
        (labels["altitude"], f"{metadata.altitude} m" if metadata.altitude is not None else None),
        (labels["resolution"], f"{metadata.width} x {metadata.height}"),
        (labels["software"], metadata.software),
        (labels["fileSize"], _format_size(metadata.file_size)),
        (labels["sha256"], metadata.sha256),
    ]


def _file_list(names: list[str]) -> TerminalResponse:
    response = TerminalResponse()
    for name in names:
        response.add(name, "muted")
    return response


def _format_size(size: int) -> str:
    if size < 1024 * 1024:
        return f"{size / 1024:.1f} KB".replace(".", ",")
    return f"{size / 1024 / 1024:.1f} MB".replace(".", ",")
