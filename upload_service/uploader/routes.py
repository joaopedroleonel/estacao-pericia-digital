from __future__ import annotations

import hmac
import re
from functools import wraps
from typing import Callable
from uuid import uuid4

from flask import Blueprint, abort, current_app, jsonify, render_template, request

from uploader.images import InvalidImageError, build_upload_name, detect_extension


PENDING_FOLDER = "pending"

UPLOAD_ID = re.compile(r"[0-9a-f]{32}")

upload_bp = Blueprint("upload", __name__)


def camera_token_required(view: Callable) -> Callable:
    @wraps(view)
    def wrapper(*args, **kwargs):
        received = request.args.get("token", "").encode()
        if not hmac.compare_digest(received, current_app.config["CAMERA_TOKEN"].encode()):
            abort(403)
        return view(*args, **kwargs)

    return wrapper


@upload_bp.get("/camera")
@camera_token_required
def camera_page():
    return render_template("camera.html")


@upload_bp.post("/api/uploads")
@camera_token_required
def create_upload():
    upload_id = uuid4().hex
    upload_url = current_app.extensions["storage"].create_upload_url(_pending_path(upload_id))
    return jsonify(uploadId=upload_id, uploadUrl=upload_url), 201


@upload_bp.post("/api/uploads/<upload_id>/confirm")
@camera_token_required
def confirm_upload(upload_id: str):
    if not UPLOAD_ID.fullmatch(upload_id):
        abort(404)
    storage = current_app.extensions["storage"]
    pending_path = _pending_path(upload_id)
    data = storage.download(pending_path)
    try:
        extension = detect_extension(data)
    except InvalidImageError:
        storage.delete([pending_path])
        return jsonify(error="invalid_image"), 400
    name = build_upload_name(extension)
    storage.move(pending_path, name)
    return jsonify(status="ok", name=name), 201


def _pending_path(upload_id: str) -> str:
    return f"{PENDING_FOLDER}/{upload_id}"
