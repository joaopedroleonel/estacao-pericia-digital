from __future__ import annotations

from typing import Iterable

import requests


class StorageError(Exception):
    pass


class StorageNotFoundError(StorageError):
    pass


class SupabaseStorage:
    def __init__(self, url: str, key: str, bucket: str, timeout: int) -> None:
        self.base_url = f"{url.rstrip('/')}/storage/v1"
        self.bucket = bucket
        self.timeout = timeout
        self.session = requests.Session()
        self.session.headers["apikey"] = key
        if key.startswith("eyJ"):
            self.session.headers["Authorization"] = f"Bearer {key}"

    def create_upload_url(self, path: str) -> str:
        response = self._request("POST", f"/object/upload/sign/{self.bucket}/{path}", json={})
        return f"{self.base_url}{response.json()['url']}"

    def download(self, path: str) -> bytes:
        return self._request("GET", f"/object/{self.bucket}/{path}").content

    def move(self, source: str, destination: str) -> None:
        payload = {"bucketId": self.bucket, "sourceKey": source, "destinationKey": destination}
        self._request("POST", "/object/move", json=payload)

    def delete(self, paths: Iterable[str]) -> None:
        self._request("DELETE", f"/object/{self.bucket}", json={"prefixes": list(paths)})

    def _request(self, method: str, path: str, **kwargs) -> requests.Response:
        try:
            response = self.session.request(method, f"{self.base_url}{path}", timeout=self.timeout, **kwargs)
        except requests.RequestException as error:
            raise StorageError(str(error)) from error
        if response.status_code == 404 or "not_found" in response.text.lower():
            raise StorageNotFoundError(path)
        if not response.ok:
            raise StorageError(f"{response.status_code} {response.text[:200]}")
        return response
