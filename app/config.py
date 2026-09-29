import os
from pathlib import Path

from dotenv import load_dotenv


BASE_DIR = Path(__file__).resolve().parent.parent

load_dotenv(BASE_DIR / ".env")


class Config:
    SECRET_KEY = os.environ.get("SECRET_KEY", "")
    ACCESS_CODE = os.environ.get("ACCESS_CODE", "")
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
    LOGIN_MAX_ATTEMPTS = 5
    LOGIN_LOCK_SECONDS = 300
    SESSION_COOKIE_SAMESITE = "Lax"


REQUIRED_SETTINGS = ("SECRET_KEY", "ACCESS_CODE")
