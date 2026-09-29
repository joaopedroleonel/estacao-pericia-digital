import pytest

from app.services.adb import AdbError
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


@pytest.fixture
def run(app, logged_client, photo_factory):
    app.extensions["adb"] = FakeAdb(photo_factory)

    def send(command):
        response = logged_client.post("/api/terminal", json={"command": command})
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


def test_open_serves_preview(run, logged_client, uploaded_photo):
    result = run(f"open {uploaded_photo.name}")
    assert texts(result) == ["imagem carregada · GPS encontrado"]
    preview = logged_client.get(result["state"]["image"]["previewUrl"])
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


def test_terminal_requires_json(logged_client):
    assert logged_client.post("/api/terminal", data="help").status_code == 415
