import os
from pathlib import Path

from dotenv import load_dotenv


BASE_DIR = Path(__file__).resolve().parent.parent

load_dotenv(BASE_DIR / ".env")


class Config:
    SECRET_KEY = os.environ.get("SECRET_KEY", "")
    ACCESS_CODE = os.environ.get("ACCESS_CODE", "")
    CAMERA_TOKEN = os.environ.get("CAMERA_TOKEN", "")
    TIMELINE_DATE = os.environ.get("TIMELINE_DATE", "")
    ADB_PATH = os.environ.get("ADB_PATH", "adb")
    DATA_DIR = BASE_DIR / "data"
    ADB_TIMEOUT_SECONDS = 10
    DEVICE_CAMERA_DIR = "/sdcard/DCIM/Camera"
    PHOTOS_LIST_LIMIT = 10
    PREVIEW_MAX_SIZE = 1600
    MAX_CONTENT_LENGTH = 25 * 1024 * 1024
    LOGIN_MAX_ATTEMPTS = 5
    LOGIN_LOCK_SECONDS = 300
    SESSION_COOKIE_SAMESITE = "Lax"


REQUIRED_SETTINGS = ("SECRET_KEY", "ACCESS_CODE", "CAMERA_TOKEN")
