import os
import secrets
from pathlib import Path

from dotenv import load_dotenv


BASE_DIR = Path(__file__).resolve().parent.parent

load_dotenv(BASE_DIR / ".env")


class Config:
    SECRET_KEY = secrets.token_hex(32)
    TIMELINE_DATE = os.environ.get("TIMELINE_DATE", "")
    ADB_PATH = os.environ.get("ADB_PATH", "adb")
    SUPABASE_URL = os.environ.get("SUPABASE_URL", "")
    SUPABASE_SECRET_KEY = os.environ.get("SUPABASE_SECRET_KEY", "")
    SUPABASE_BUCKET = os.environ.get("SUPABASE_BUCKET", "uploads")
    DATA_DIR = BASE_DIR / "data"
    ADB_TIMEOUT_SECONDS = 10
    DEVICE_CAMERA_DIR = "/sdcard/DCIM/Camera"
    PHOTOS_LIST_LIMIT = 10
    PREVIEW_MAX_SIZE = 1600
    CLOUD_TIMEOUT_SECONDS = 20
    SESSION_COOKIE_SAMESITE = "Lax"

