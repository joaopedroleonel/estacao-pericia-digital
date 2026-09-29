import os
from pathlib import Path

from dotenv import load_dotenv


BASE_DIR = Path(__file__).resolve().parent.parent

load_dotenv(BASE_DIR / ".env")


class Config:
    CAMERA_TOKEN = os.environ.get("CAMERA_TOKEN", "")
    SUPABASE_URL = os.environ.get("SUPABASE_URL", "")
    SUPABASE_SECRET_KEY = os.environ.get("SUPABASE_SECRET_KEY", "")
    SUPABASE_BUCKET = os.environ.get("SUPABASE_BUCKET", "uploads")
    STORAGE_TIMEOUT_SECONDS = 20


REQUIRED_SETTINGS = ("CAMERA_TOKEN", "SUPABASE_URL", "SUPABASE_SECRET_KEY")
