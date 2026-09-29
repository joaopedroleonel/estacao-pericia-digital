import io
import re

from PIL import Image


def login(client, code):
    return client.post("/login", data={"code": code})


def test_login_page_is_public(client):
    assert client.get("/login").status_code == 200


def test_dashboard_redirects_without_session(client):
    response = client.get("/")
    assert response.status_code == 302
    assert response.headers["Location"].endswith("/login")


def test_login_with_correct_code(client):
    response = login(client, "1234")
    assert response.status_code == 302
    assert client.get("/").status_code == 200


def test_login_with_wrong_code(client):
    assert login(client, "0000").status_code == 401


def test_login_locks_after_five_failures(client):
    statuses = [login(client, "0000").status_code for _ in range(5)]
    assert statuses == [401, 401, 401, 401, 429]
    assert login(client, "1234").status_code == 429


def test_logout_clears_session(logged_client):
    logged_client.get("/logout")
    assert logged_client.get("/").status_code == 302


def test_api_requires_session(client):
    for response in (client.get("/api/timeline"), client.post("/api/terminal", json={"command": "help"})):
        assert response.status_code == 401
        assert response.get_json() == {"error": "unauthorized"}


def test_timeline_endpoint(logged_client):
    payload = logged_client.get("/api/timeline").get_json()
    assert len(payload["points"]) == 4
    assert len(payload["visits"]) == 1
    assert len(payload["activities"]) == 1


def test_preview_rejects_path_traversal(logged_client):
    assert logged_client.get("/api/images/..%2F..%2Fapp%2Fconfig.py").status_code == 404


def test_camera_page_requires_token(client):
    assert client.get("/camera").status_code == 403
    assert client.get("/camera?token=wrong").status_code == 403
    assert client.get("/camera?token=camera-token").status_code == 200


def test_upload_requires_token(client):
    response = client.post("/api/upload?token=wrong", data={"photo": (io.BytesIO(b"x"), "a.jpg")})
    assert response.status_code == 403
    assert response.get_json() == {"error": "forbidden"}


def test_upload_rejects_non_images(client):
    response = client.post("/api/upload?token=camera-token", data={"photo": (io.BytesIO(b"not an image"), "a.jpg")})
    assert response.status_code == 400
    assert response.get_json() == {"error": "invalid_image"}


def test_upload_rejects_missing_file(client):
    response = client.post("/api/upload?token=camera-token", data={})
    assert response.get_json() == {"error": "missing_file"}


def test_upload_rejects_large_files(app, client):
    app.config["MAX_CONTENT_LENGTH"] = 1024
    response = client.post("/api/upload?token=camera-token", data={"photo": (io.BytesIO(b"x" * 4096), "a.jpg")})
    assert response.status_code == 413
    assert response.get_json() == {"error": "too_large"}


def test_upload_accepts_heic(app, client):
    buffer = io.BytesIO()
    Image.new("RGB", (32, 32), "gray").save(buffer, format="HEIF")
    buffer.seek(0)
    response = client.post("/api/upload?token=camera-token", data={"photo": (buffer, "IMG_0001.HEIC")})
    assert response.status_code == 201
    assert response.get_json()["name"].endswith(".heic")


def test_upload_accepts_iphone_hdr_jpeg(app, client):
    buffer = io.BytesIO()
    main, gain_map = Image.new("RGB", (32, 32), "gray"), Image.new("L", (16, 16), "white")
    main.save(buffer, format="MPO", save_all=True, append_images=[gain_map])
    original = buffer.getvalue()
    response = client.post("/api/upload?token=camera-token", data={"photo": (io.BytesIO(original), "IMG_0631.jpeg")})
    assert response.status_code == 201
    name = response.get_json()["name"]
    assert name.endswith(".jpg")
    assert (app.config["UPLOADS_DIR"] / name).read_bytes() == original


def test_upload_keeps_original_bytes(app, client, photo_factory, tmp_path):
    original = photo_factory(tmp_path / "original.jpg").read_bytes()
    response = client.post(
        "/api/upload?token=camera-token",
        data={"photo": (io.BytesIO(original), "whatever.png")},
    )
    assert response.status_code == 201
    name = response.get_json()["name"]
    assert re.fullmatch(r"upload_\d{8}_\d{6}_[0-9a-f]{4}\.jpg", name)
    assert (app.config["UPLOADS_DIR"] / name).read_bytes() == original
