from __future__ import annotations

from pathlib import Path

from flask import Flask

from app.auth import LoginLimiter
from app.config import REQUIRED_SETTINGS, Config
from app.routes import register_blueprints, register_error_handlers
from app.services.adb import AdbService
from app.services.cloud_storage import CloudStorage
from app.services.timeline import Timeline, load_timeline


def create_app(overrides: dict | None = None) -> Flask:
    app = Flask(__name__)
    app.config.from_object(Config)
    app.config.update(overrides or {})
    _check_required_settings(app)
    _prepare_data_dirs(app)
    app.extensions["login_limiter"] = LoginLimiter(
        app.config["LOGIN_MAX_ATTEMPTS"], app.config["LOGIN_LOCK_SECONDS"]
    )
    app.extensions["adb"] = AdbService(
        app.config["ADB_PATH"], app.config["ADB_TIMEOUT_SECONDS"], app.config["DEVICE_CAMERA_DIR"]
    )
    app.extensions["timeline"] = _load_timeline(app)
    app.extensions["cloud"] = _create_cloud(app)
    register_blueprints(app)
    register_error_handlers(app)
    return app


def _check_required_settings(app: Flask) -> None:
    missing = [name for name in REQUIRED_SETTINGS if not app.config.get(name)]
    if missing:
        raise RuntimeError(f"Missing settings in .env: {', '.join(missing)}")


def _prepare_data_dirs(app: Flask) -> None:
    data_dir = Path(app.config["DATA_DIR"])
    app.config.setdefault("TIMELINE_FILE", data_dir / "timeline.json")
    for key, folder in (("EXTRACTED_DIR", "extracted"), ("UPLOADS_DIR", "uploads"), ("PREVIEWS_DIR", "previews")):
        path = app.config.setdefault(key, data_dir / folder)
        Path(path).mkdir(parents=True, exist_ok=True)


def _create_cloud(app: Flask) -> CloudStorage | None:
    if not (app.config["SUPABASE_URL"] and app.config["SUPABASE_SECRET_KEY"]):
        return None
    return CloudStorage(
        app.config["SUPABASE_URL"],
        app.config["SUPABASE_SECRET_KEY"],
        app.config["SUPABASE_BUCKET"],
        app.config["CLOUD_TIMEOUT_SECONDS"],
    )


def _load_timeline(app: Flask) -> Timeline:
    try:
        return load_timeline(Path(app.config["TIMELINE_FILE"]), app.config["TIMELINE_DATE"])
    except (OSError, ValueError) as error:
        app.logger.warning("Timeline unavailable: %s", error)
        return Timeline()
