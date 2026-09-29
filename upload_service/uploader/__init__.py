from __future__ import annotations

from flask import Flask, current_app, jsonify, render_template, request
from werkzeug.exceptions import HTTPException

from uploader.config import REQUIRED_SETTINGS, STATIC_DIR, Config
from uploader.routes import upload_bp
from uploader.storage import StorageError, StorageNotFoundError, SupabaseStorage


ERROR_CODES = {400: "bad_request", 403: "forbidden", 404: "not_found", 405: "method_not_allowed"}


def create_app(overrides: dict | None = None) -> Flask:
    app = Flask(__name__, static_folder=str(STATIC_DIR))
    app.config.from_object(Config)
    app.config.update(overrides or {})
    missing = [name for name in REQUIRED_SETTINGS if not app.config.get(name)]
    if missing:
        raise RuntimeError(f"Missing settings: {', '.join(missing)}")
    app.extensions["storage"] = SupabaseStorage(
        app.config["SUPABASE_URL"],
        app.config["SUPABASE_SECRET_KEY"],
        app.config["SUPABASE_BUCKET"],
        app.config["STORAGE_TIMEOUT_SECONDS"],
    )
    app.register_blueprint(upload_bp)
    app.register_error_handler(HTTPException, _handle_http_error)
    app.register_error_handler(StorageNotFoundError, _handle_not_found)
    app.register_error_handler(StorageError, _handle_storage_error)
    return app


def _handle_http_error(failure: HTTPException):
    if request.path.startswith("/api/"):
        return jsonify(error=ERROR_CODES.get(failure.code, "error")), failure.code
    return render_template("error.html", status=failure.code), failure.code


def _handle_not_found(failure: StorageNotFoundError):
    return jsonify(error="not_found"), 404


def _handle_storage_error(failure: StorageError):
    current_app.logger.warning("Storage request failed: %s", failure)
    return jsonify(error="storage_unavailable"), 502
