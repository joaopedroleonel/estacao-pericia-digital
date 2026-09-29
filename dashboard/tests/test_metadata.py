from datetime import datetime

from app.services.images import sha256_file
from app.services.metadata import extract_metadata


def test_extracts_summary_and_gps(tmp_path, photo_factory):
    path = photo_factory(tmp_path / "photo.jpg")
    metadata = extract_metadata(path)
    assert metadata.make == "LG"
    assert metadata.model == "LG K220"
    assert metadata.taken_at == datetime(2026, 9, 24, 14, 32)
    assert (metadata.latitude, metadata.longitude) == (-24.558, -54.056)
    assert metadata.altitude == 412.3
    assert (metadata.width, metadata.height) == (64, 48)
    assert metadata.sha256 == sha256_file(path)


def test_lists_all_tags_by_group(tmp_path, photo_factory):
    metadata = extract_metadata(photo_factory(tmp_path / "photo.jpg"))
    assert {tag["group"] for tag in metadata.tags} == {"Image", "Exif", "GPS"}
    maker_note = next(tag for tag in metadata.tags if tag["name"] == "MakerNote")
    assert maker_note == {"group": "Exif", "name": "MakerNote", "value": None, "bytes": 200}


def test_handles_photo_without_exif(tmp_path, photo_factory):
    metadata = extract_metadata(photo_factory(tmp_path / "plain.png", with_exif=False))
    assert metadata.make is None
    assert metadata.taken_at is None
    assert not metadata.has_gps
    assert metadata.tags == []
