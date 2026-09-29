from pathlib import Path

from flask import Blueprint, current_app, jsonify, render_template, request

from app.auth import camera_token_required
from app.services.images import InvalidImageError, save_upload


camera_bp = Blueprint("camera", __name__)


@camera_bp.get("/camera")
@camera_token_required
def camera_page():
    return render_template("camera.html")


@camera_bp.post("/api/upload")
@camera_token_required
def upload():
    photo = request.files.get("photo")
    if photo is None:
        return jsonify(error="missing_file"), 400
    try:
        path = save_upload(photo.read(), Path(current_app.config["UPLOADS_DIR"]))
    except InvalidImageError:
        return jsonify(error="invalid_image"), 400
    return jsonify(status="ok", name=path.name), 201
