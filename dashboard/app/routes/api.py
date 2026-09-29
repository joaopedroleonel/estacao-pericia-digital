from flask import Blueprint, current_app, jsonify, request, send_from_directory, session

from app.auth import login_required
from app.terminal import run_command
from app.terminal.response import TerminalContext


MAX_COMMAND_LENGTH = 256

api_bp = Blueprint("api", __name__)


@api_bp.post("/api/terminal")
@login_required
def terminal():
    if not request.is_json:
        return jsonify(error="unsupported_media_type"), 415
    command = (request.get_json(silent=True) or {}).get("command")
    if not isinstance(command, str) or len(command) > MAX_COMMAND_LENGTH:
        return jsonify(error="bad_request"), 400
    context = TerminalContext(
        config=current_app.config,
        adb=current_app.extensions["adb"],
        timeline=current_app.extensions["timeline"],
        cloud=current_app.extensions["cloud"],
        session=session,
    )
    return jsonify(run_command(command, context).to_dict())


@api_bp.get("/api/images/<name>")
@login_required
def image_preview(name: str):
    return send_from_directory(current_app.config["PREVIEWS_DIR"], name)


@api_bp.get("/api/timeline")
@login_required
def timeline():
    return jsonify(current_app.extensions["timeline"].to_dict())
