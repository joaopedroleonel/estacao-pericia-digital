import pytest

from app.services.adb import AdbError
from app.services.cloud_storage import CloudError
from app.services.images import sha256_file


class FakeAdb:
    def __init__(self, photo_factory, failure=None):
        self.photo_factory = photo_factory
        self.failure = failure

    def get_device_info(self):
        self._raise_failure()
        return {"manufacturer": "Xiaomi", "model": "Redmi Note 8", "androidVersion": "11"}

    def list_camera_photos(self, limit):
        self._raise_failure()
        return ["IMG_20260924_1510.jpg", "IMG_20260924_1432.jpg"][:limit]

    def pull_photo(self, name, destination):
        self._raise_failure()
        return self.photo_factory(destination / name)

    def _raise_failure(self):
        if self.failure:
            raise AdbError(self.failure)


class FakeCloud:
    def __init__(self, files=None, failing=False):
        self.files = dict(files or {})
        self.failing = failing

    def list_files(self):
        self._raise_failure()
        return sorted(self.files)

    def download(self, name):
        self._raise_failure()
        return self.files[name]

    def delete(self, names):
        self._raise_failure()
        for name in names:
            self.files.pop(name, None)

    def _raise_failure(self):
        if self.failing:
            raise CloudError("offline")


@pytest.fixture
def run(app, client, photo_factory):
    app.extensions["adb"] = FakeAdb(photo_factory)

    def send(command):
        response = client.post("/api/terminal", json={"command": command})
        assert response.status_code == 200
        return response.get_json()

    return send


@pytest.fixture
def uploaded_photo(app, photo_factory):
    return photo_factory(app.config["UPLOADS_DIR"] / "upload_20260924_143200_a8f3.jpg")


def texts(result):
    return [line["text"] for line in result["output"]]


def styles(result):
    return [line["style"] for line in result["output"]]


def test_help_lists_commands(run):
    output = "\n".join(texts(run("help")))
    for command in ("device", "pull <file>", "open <file>", "map route", "map photo", "clear"):
        assert command in output


def test_rejects_unknown_command(run):
    assert styles(run("rm -rf /")) == ["error"]


def test_validates_argument_count(run):
    assert texts(run("open")) == ["uso: open <file>"]


def test_rejects_unbalanced_quotes(run):
    assert styles(run('open "IMG.jpg')) == ["error"]


def test_empty_command_returns_nothing(run):
    assert run("   ") == {"output": [], "state": {}}


def test_shows_device_info(run):
    assert texts(run("device")) == ["Xiaomi Redmi Note 8 · Android 11"]


def test_translates_adb_errors(app, run, photo_factory):
    app.extensions["adb"] = FakeAdb(photo_factory, failure="no_device")
    result = run("device")
    assert styles(result) == ["error"]
    assert "celular" in texts(result)[0]


def test_lists_device_photos(run):
    assert texts(run("photos")) == ["IMG_20260924_1510.jpg", "IMG_20260924_1432.jpg"]


def test_pull_rejects_unsafe_names(run):
    assert styles(run("pull ../secret.jpg")) == ["error"]


def test_pull_copies_photo_and_shows_hash(app, run):
    result = run("pull IMG_20260924_1432.jpg")
    path = app.config["EXTRACTED_DIR"] / "IMG_20260924_1432.jpg"
    assert path.is_file()
    assert styles(result)[0] == "success"
    assert texts(result)[1] == f"{sha256_file(path)}  IMG_20260924_1432.jpg"


def test_lists_extracted_photos(run):
    assert styles(run("extracted")) == ["error"]
    run("pull IMG_20260924_1432.jpg")
    assert texts(run("extracted")) == ["IMG_20260924_1432.jpg"]


def test_uploads_and_latest_without_photos(run):
    assert styles(run("uploads")) == ["error"]
    assert styles(run("latest")) == ["error"]


def test_latest_opens_newest_upload(run, uploaded_photo):
    result = run("latest")
    image = result["state"]["image"]
    assert image["name"] == uploaded_photo.name
    assert image["summary"]["gps"] == {"lat": -24.558, "lng": -54.056}
    assert result["state"]["map"] == {"action": "photo", "lat": -24.558, "lng": -54.056}


def test_open_serves_preview(run, client, uploaded_photo):
    result = run(f"open {uploaded_photo.name}")
    assert texts(result) == ["imagem carregada · GPS encontrado"]
    preview = client.get(result["state"]["image"]["previewUrl"])
    assert preview.status_code == 200
    assert preview.mimetype == "image/jpeg"


def test_open_missing_image(run):
    assert styles(run("open missing.jpg")) == ["error"]


def test_open_image_without_gps_keeps_map(app, run, photo_factory):
    photo_factory(app.config["EXTRACTED_DIR"] / "plain.jpg", with_gps=False)
    result = run("open plain.jpg")
    assert texts(result) == ["imagem carregada · sem GPS"]
    assert "map" not in result["state"]
    assert styles(run("map photo")) == ["error"]


def test_clear_uploads_deletes_photos_and_previews(app, run, uploaded_photo, photo_factory):
    photo_factory(app.config["UPLOADS_DIR"] / "upload_20260924_150000_b1c2.jpg")
    run(f"open {uploaded_photo.name}")
    result = run("clear-uploads")
    assert texts(result) == ["2 foto(s) apagada(s) de uploads"]
    assert list(app.config["UPLOADS_DIR"].iterdir()) == []
    assert list(app.config["PREVIEWS_DIR"].iterdir()) == []
    assert styles(run("exif")) == ["error"]


def test_clear_uploads_without_photos(run):
    assert styles(run("clear-uploads")) == ["error"]


def test_clear_uploads_keeps_extracted_photos(app, run, photo_factory, uploaded_photo):
    extracted = photo_factory(app.config["EXTRACTED_DIR"] / "IMG_20260924_1432.jpg")
    run("clear-uploads")
    assert extracted.exists()


def test_exif_and_hash_need_open_image(run):
    assert styles(run("exif")) == ["error"]
    assert styles(run("hash")) == ["error"]


def test_exif_and_hash_describe_open_image(run, uploaded_photo):
    run(f"open {uploaded_photo.name}")
    assert any("LG K220" in line for line in texts(run("exif")))
    assert texts(run("hash")) == [f"{sha256_file(uploaded_photo)}  {uploaded_photo.name}"]


def test_map_commands(run, uploaded_photo):
    assert run("map route")["state"]["map"] == {"action": "route"}
    run(f"open {uploaded_photo.name}")
    assert run("map photo")["state"]["map"] == {"action": "photo", "lat": -24.558, "lng": -54.056}


def test_terminal_requires_json(client):
    assert client.post("/api/terminal", data="help").status_code == 415


def test_uploads_downloads_and_removes_cloud_files(app, run, tmp_path, photo_factory):
    photo = photo_factory(tmp_path / "cloud.jpg").read_bytes()
    cloud = FakeCloud({"upload_20260929_101000_aaaa.jpg": photo})
    app.extensions["cloud"] = cloud
    result = run("uploads")
    assert texts(result) == ["1 foto(s) nova(s) baixada(s) da nuvem", "upload_20260929_101000_aaaa.jpg"]
    assert (app.config["UPLOADS_DIR"] / "upload_20260929_101000_aaaa.jpg").read_bytes() == photo
    assert cloud.files == {}


def test_sync_keeps_existing_local_file_and_clears_cloud(app, run, uploaded_photo):
    original = uploaded_photo.read_bytes()
    cloud = FakeCloud({uploaded_photo.name: b"other bytes"})
    app.extensions["cloud"] = cloud
    assert texts(run("uploads")) == [uploaded_photo.name]
    assert uploaded_photo.read_bytes() == original
    assert cloud.files == {}


def test_sync_failure_still_lists_local_photos(app, run, uploaded_photo):
    app.extensions["cloud"] = FakeCloud({"upload_x.jpg": b""}, failing=True)
    result = run("uploads")
    assert texts(result) == ["não foi possível sincronizar com a nuvem", uploaded_photo.name]
    assert styles(result)[0] == "error"


def test_latest_opens_photo_downloaded_from_cloud(app, run, uploaded_photo, tmp_path, photo_factory):
    photo = photo_factory(tmp_path / "cloud.jpg").read_bytes()
    app.extensions["cloud"] = FakeCloud({"upload_20260929_110000_bbbb.jpg": photo})
    result = run("latest")
    assert texts(result)[0] == "1 foto(s) nova(s) baixada(s) da nuvem"
    assert result["state"]["image"]["name"] == "upload_20260929_110000_bbbb.jpg"
