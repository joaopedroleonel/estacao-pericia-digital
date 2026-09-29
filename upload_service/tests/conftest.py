from io import BytesIO

import pytest
from PIL import ExifTags, Image

from uploader import create_app
from uploader.storage import StorageError, StorageNotFoundError


class FakeStorage:
    def __init__(self) -> None:
        self.objects: dict[str, bytes] = {}
        self.failing = False

    def create_upload_url(self, path: str) -> str:
        self._check()
        return f"https://storage.test/object/upload/sign/uploads/{path}?token=signed"

    def download(self, path: str) -> bytes:
        self._check()
        if path not in self.objects:
            raise StorageNotFoundError(path)
        return self.objects[path]

    def move(self, source: str, destination: str) -> None:
        self._check()
        self.objects[destination] = self.objects.pop(source)

    def delete(self, paths) -> None:
        self._check()
        for path in paths:
            self.objects.pop(path, None)

    def _check(self) -> None:
        if self.failing:
            raise StorageError("offline")


def image_bytes(image_format: str) -> bytes:
    buffer = BytesIO()
    image = Image.new("RGB", (32, 24), "gray")
    if image_format == "JPEG":
        exif = Image.Exif()
        exif[ExifTags.Base.Make] = "Apple"
        exif[ExifTags.Base.Model] = "iPhone 14 Pro Max"
        image.save(buffer, "JPEG", exif=exif)
    elif image_format == "MPO":
        image.save(buffer, "MPO", save_all=True, append_images=[Image.new("L", (16, 12), "white")])
    else:
        image.save(buffer, image_format)
    return buffer.getvalue()


@pytest.fixture
def storage():
    return FakeStorage()


@pytest.fixture
def app(storage):
    app = create_app(
        {
            "TESTING": True,
            "CAMERA_TOKEN": "camera-token",
            "SUPABASE_URL": "https://project.supabase.test",
            "SUPABASE_SECRET_KEY": "sb_secret_test",
        }
    )
    app.extensions["storage"] = storage
    return app


@pytest.fixture
def client(app):
    return app.test_client()
