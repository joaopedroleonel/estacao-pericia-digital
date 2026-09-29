import pytest
import requests

from app.services.cloud_storage import CloudError, CloudStorage


class FakeResponse:
    def __init__(self, status_code, payload=None, content=b""):
        self.status_code = status_code
        self.ok = status_code < 400
        self.payload = payload
        self.content = content
        self.text = str(payload)

    def json(self):
        return self.payload


@pytest.fixture
def calls(monkeypatch):
    recorded = []
    responses = []

    def fake_request(self, method, url, **kwargs):
        recorded.append((method, url, kwargs))
        response = responses.pop(0)
        if isinstance(response, Exception):
            raise response
        return response

    monkeypatch.setattr(requests.Session, "request", fake_request)
    return recorded, responses


def make_cloud():
    return CloudStorage("https://project.supabase.co", "sb_secret_abc", "uploads", 5)


def test_list_files_keeps_only_safe_root_files(calls):
    recorded, responses = calls
    responses.append(FakeResponse(200, [
        {"name": "pending", "id": None},
        {"name": "upload_20260929_101000_aaaa.jpg", "id": "1"},
        {"name": "../evil.jpg", "id": "2"},
        {"name": "notes.txt", "id": "3"},
    ]))
    assert make_cloud().list_files() == ["upload_20260929_101000_aaaa.jpg"]
    method, url, kwargs = recorded[0]
    assert (method, url) == ("POST", "https://project.supabase.co/storage/v1/object/list/uploads")
    assert kwargs["json"]["prefix"] == ""


def test_download_and_delete_requests(calls):
    recorded, responses = calls
    responses.extend([FakeResponse(200, content=b"bytes"), FakeResponse(200, [])])
    cloud = make_cloud()
    assert cloud.download("upload_1.jpg") == b"bytes"
    cloud.delete(["upload_1.jpg"])
    assert recorded[0][:2] == ("GET", "https://project.supabase.co/storage/v1/object/uploads/upload_1.jpg")
    assert recorded[1][:2] == ("DELETE", "https://project.supabase.co/storage/v1/object/uploads")
    assert recorded[1][2]["json"] == {"prefixes": ["upload_1.jpg"]}


def test_errors_become_cloud_error(calls):
    _, responses = calls
    responses.extend([FakeResponse(500, {"error": "internal"}), requests.ConnectionError("offline")])
    cloud = make_cloud()
    with pytest.raises(CloudError):
        cloud.download("x.jpg")
    with pytest.raises(CloudError):
        cloud.list_files()
