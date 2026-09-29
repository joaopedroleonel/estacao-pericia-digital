import re

import pytest
from conftest import image_bytes


UPLOAD_NAME = re.compile(r"upload_\d{8}_\d{6}_[0-9a-f]{4}\.(jpg|png|webp|heic)")


def start_upload(client, data, storage):
    response = client.post("/api/uploads?token=camera-token")
    assert response.status_code == 201
    upload_id = response.get_json()["uploadId"]
    storage.objects[f"pending/{upload_id}"] = data
    return upload_id


def test_camera_page_requires_token(client):
    assert client.get("/camera").status_code == 403
    assert client.get("/camera?token=wrong").status_code == 403
    assert client.get("/camera?token=camera-token").status_code == 200


def test_api_requires_token(client):
    response = client.post("/api/uploads?token=wrong")
    assert response.status_code == 403
    assert response.get_json() == {"error": "forbidden"}


def test_create_upload_returns_signed_url_for_pending_path(client):
    payload = client.post("/api/uploads?token=camera-token").get_json()
    assert re.fullmatch(r"[0-9a-f]{32}", payload["uploadId"])
    assert f"/pending/{payload['uploadId']}?token=" in payload["uploadUrl"]


@pytest.mark.parametrize(("image_format", "extension"), [("JPEG", ".jpg"), ("MPO", ".jpg"), ("PNG", ".png"), ("HEIF", ".heic")])
def test_confirm_moves_valid_image_with_original_bytes(client, storage, image_format, extension):
    original = image_bytes(image_format)
    upload_id = start_upload(client, original, storage)
    response = client.post(f"/api/uploads/{upload_id}/confirm?token=camera-token")
    assert response.status_code == 201
    name = response.get_json()["name"]
    assert UPLOAD_NAME.fullmatch(name)
    assert name.endswith(extension)
    assert storage.objects == {name: original}


def test_confirm_deletes_invalid_file(client, storage):
    upload_id = start_upload(client, b"not an image", storage)
    response = client.post(f"/api/uploads/{upload_id}/confirm?token=camera-token")
    assert response.status_code == 400
    assert response.get_json() == {"error": "invalid_image"}
    assert storage.objects == {}


@pytest.mark.parametrize("upload_id", ["0" * 32, "../secret", "abc"])
def test_confirm_unknown_or_malformed_upload(client, upload_id):
    response = client.post(f"/api/uploads/{upload_id}/confirm?token=camera-token")
    assert response.status_code == 404


def test_storage_failure_returns_502(client, storage):
    storage.failing = True
    response = client.post("/api/uploads?token=camera-token")
    assert response.status_code == 502
    assert response.get_json() == {"error": "storage_unavailable"}
