from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path

from PIL import ExifTags, Image, TiffImagePlugin

from app.services.images import sha256_file
from app.utils import dms_to_decimal


IFD_POINTERS = {ExifTags.IFD.Exif, ExifTags.IFD.GPSInfo}

MAX_TEXT_LENGTH = 200

MAX_INLINE_BYTES = 64


@dataclass
class ImageMetadata:
    name: str
    width: int
    height: int
    file_size: int
    sha256: str
    make: str | None = None
    model: str | None = None
    taken_at: datetime | None = None
    software: str | None = None
    latitude: float | None = None
    longitude: float | None = None
    altitude: float | None = None
    tags: list[dict] = field(default_factory=list)

    @property
    def has_gps(self) -> bool:
        return self.latitude is not None and self.longitude is not None

    def summary(self) -> dict:
        return {
            "make": self.make,
            "model": self.model,
            "takenAt": self.taken_at.isoformat() if self.taken_at else None,
            "gps": {"lat": self.latitude, "lng": self.longitude} if self.has_gps else None,
            "altitude": self.altitude,
            "width": self.width,
            "height": self.height,
            "software": self.software,
            "fileSize": self.file_size,
            "sha256": self.sha256,
        }


def extract_metadata(path: Path) -> ImageMetadata:
    with Image.open(path) as image:
        width, height = image.size
        exif = image.getexif()
        base_tags = {key: value for key, value in exif.items() if key not in IFD_POINTERS}
        exif_tags = dict(exif.get_ifd(ExifTags.IFD.Exif))
        gps_tags = dict(exif.get_ifd(ExifTags.IFD.GPSInfo))
    return ImageMetadata(
        name=path.name,
        width=width,
        height=height,
        file_size=path.stat().st_size,
        sha256=sha256_file(path),
        make=_text(base_tags.get(ExifTags.Base.Make)),
        model=_text(base_tags.get(ExifTags.Base.Model)),
        taken_at=_parse_exif_date(exif_tags.get(ExifTags.Base.DateTimeOriginal) or base_tags.get(ExifTags.Base.DateTime)),
        software=_text(base_tags.get(ExifTags.Base.Software)),
        latitude=dms_to_decimal(gps_tags.get(ExifTags.GPS.GPSLatitude), gps_tags.get(ExifTags.GPS.GPSLatitudeRef)),
        longitude=dms_to_decimal(gps_tags.get(ExifTags.GPS.GPSLongitude), gps_tags.get(ExifTags.GPS.GPSLongitudeRef)),
        altitude=_parse_altitude(gps_tags),
        tags=[
            *_describe_tags("Image", base_tags, ExifTags.TAGS),
            *_describe_tags("Exif", exif_tags, ExifTags.TAGS),
            *_describe_tags("GPS", gps_tags, ExifTags.GPSTAGS),
        ],
    )


def _describe_tags(group: str, tags: dict, names: dict) -> list[dict]:
    return [_describe_tag(group, names.get(key, f"0x{key:04X}"), value) for key, value in tags.items()]


def _describe_tag(group: str, name: str, value: object) -> dict:
    if isinstance(value, bytes) and len(value) > MAX_INLINE_BYTES:
        return {"group": group, "name": name, "value": None, "bytes": len(value)}
    return {"group": group, "name": name, "value": _format_value(value)}


def _format_value(value: object) -> str:
    if isinstance(value, bytes):
        return value.decode("latin-1").strip("\x00 ")
    if isinstance(value, TiffImagePlugin.IFDRational):
        return _format_rational(value)
    if isinstance(value, tuple):
        return ", ".join(_format_value(item) for item in value)
    return str(value).strip("\x00 ")[:MAX_TEXT_LENGTH]


def _format_rational(value: TiffImagePlugin.IFDRational) -> str:
    if not value.denominator:
        return ""
    if value.numerator == 1 and value.denominator > 1:
        return f"1/{value.denominator}"
    return f"{float(value):g}"


def _text(value: object) -> str | None:
    if value is None:
        return None
    return _format_value(value) or None


def _parse_exif_date(value: object) -> datetime | None:
    try:
        return datetime.strptime(str(value).strip("\x00 "), "%Y:%m:%d %H:%M:%S")
    except ValueError:
        return None


def _parse_altitude(gps_tags: dict) -> float | None:
    altitude = gps_tags.get(ExifTags.GPS.GPSAltitude)
    if altitude is None or not getattr(altitude, "denominator", 1):
        return None
    reference = gps_tags.get(ExifTags.GPS.GPSAltitudeRef, 0)
    below_sea_level = reference in (1, b"\x01")
    return round(-float(altitude) if below_sea_level else float(altitude), 1)
