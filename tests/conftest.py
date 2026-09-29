import shutil
from pathlib import Path

import pytest
from PIL import ExifTags, Image

from app import create_app


FIXTURES_DIR = Path(__file__).parent / "fixtures"

MAKER_NOTE = b"\x01" * 200


def create_photo(path: Path, with_exif: bool = True, with_gps: bool = True) -> Path:
    image = Image.new("RGB", (64, 48), "gray")
    if not with_exif:
        image.save(path)
        return path
    exif = Image.Exif()
    exif[ExifTags.Base.Make] = "LG"
    exif[ExifTags.Base.Model] = "LG K220"
    exif[ExifTags.IFD.Exif] = {
        ExifTags.Base.DateTimeOriginal: "2026:09:24 14:32:00",
        ExifTags.Base.MakerNote: MAKER_NOTE,
    }
    if with_gps:
        exif[ExifTags.IFD.GPSInfo] = {
            ExifTags.GPS.GPSLatitudeRef: "S",
            ExifTags.GPS.GPSLatitude: (24.0, 33.0, 28.8),
            ExifTags.GPS.GPSLongitudeRef: "W",
            ExifTags.GPS.GPSLongitude: (54.0, 3.0, 21.6),
            ExifTags.GPS.GPSAltitude: 412.3,
        }
    image.save(path, "JPEG", exif=exif)
    return path


@pytest.fixture
def photo_factory():
    return create_photo


@pytest.fixture
def app(tmp_path):
    shutil.copy(FIXTURES_DIR / "timeline_sample.json", tmp_path / "timeline.json")
    return create_app(
        {
            "TESTING": True,
            "SECRET_KEY": "test-secret",
            "ACCESS_CODE": "1234",
            "SUPABASE_URL": "",
            "SUPABASE_SECRET_KEY": "",
            "TIMELINE_DATE": "2026-09-24",
            "DATA_DIR": tmp_path,
        }
    )


@pytest.fixture
def client(app):
    return app.test_client()


@pytest.fixture
def logged_client(client):
    with client.session_transaction() as session:
        session["authenticated"] = True
    return client
