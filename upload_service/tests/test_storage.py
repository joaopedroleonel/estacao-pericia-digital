from __future__ import annotations

import pytest
import requests

from uploader.storage import StorageError, StorageNotFoundError, SupabaseStorage


class FakeResponse:
    def __init__(self, status_code: int, payload: dict | None = None, content: bytes = b"") -> None:
        self.status_code = status_code
        self.ok = status_code < 400
        self.payload = payload or {}
        self.content = content
        self.text = str(payload or "")

    def json(self) -> dict:
        return self.payload


@pytest.fixture
def calls(monkeypatch):
    recorded = []
    responses = []

    def fake_request(self, method, url, **kwargs):
        recorded.append((method, url, kwargs, dict(self.headers)))
        response = responses.pop(0)
        if isinstance(response, Exception):
            raise response
        return response

    monkeypatch.setattr(requests.Session, "request", fake_request)
    return recorded, responses


def make_storage(key: str = "sb_secret_abc") -> SupabaseStorage:
    return SupabaseStorage("https://project.supabase.co/", key, "uploads", 5)


def test_create_upload_url_builds_full_signed_url(calls):
    recorded, responses = calls
    responses.append(FakeResponse(200, {"url": "/object/upload/sign/uploads/pending/abc?token=xyz"}))
    url = make_storage().create_upload_url("pending/abc")
    assert url == "https://project.supabase.co/storage/v1/object/upload/sign/uploads/pending/abc?token=xyz"
    method, request_url, _, _ = recorded[0]
    assert (method, request_url) == ("POST", "https://project.supabase.co/storage/v1/object/upload/sign/uploads/pending/abc")


def test_secret_key_uses_only_apikey_header(calls):
    recorded, responses = calls
    responses.append(FakeResponse(200, content=b"data"))
    make_storage("sb_secret_abc").download("x.jpg")
    headers = recorded[0][3]
    assert headers["apikey"] == "sb_secret_abc"
    assert "Authorization" not in headers


def test_legacy_jwt_key_also_sends_bearer(calls):
    recorded, responses = calls
    responses.append(FakeResponse(200, content=b"data"))
    make_storage("eyJhbGciOi.test").download("x.jpg")
    assert recorded[0][3]["Authorization"] == "Bearer eyJhbGciOi.test"


def test_move_and_delete_payloads(calls):
    recorded, responses = calls
    responses.extend([FakeResponse(200), FakeResponse(200)])
    storage = make_storage()
    storage.move("pending/abc", "upload_1.jpg")
    storage.delete(["pending/abc"])
    assert recorded[0][2]["json"] == {"bucketId": "uploads", "sourceKey": "pending/abc", "destinationKey": "upload_1.jpg"}
    assert recorded[1][:2] == ("DELETE", "https://project.supabase.co/storage/v1/object/uploads")
    assert recorded[1][2]["json"] == {"prefixes": ["pending/abc"]}


def test_errors_are_translated(calls):
    _, responses = calls
    responses.extend([
        FakeResponse(400, {"statusCode": "404", "error": "not_found"}),
        FakeResponse(500, {"error": "internal"}),
        requests.ConnectionError("offline"),
    ])
    storage = make_storage()
    with pytest.raises(StorageNotFoundError):
        storage.download("missing.jpg")
    with pytest.raises(StorageError):
        storage.download("x.jpg")
    with pytest.raises(StorageError):
        storage.download("x.jpg")
