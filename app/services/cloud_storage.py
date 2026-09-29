from __future__ import annotations

from pathlib import Path
from typing import Iterable

import requests

from app.utils import is_safe_filename


LIST_LIMIT = 1000


class CloudError(Exception):
    pass


class CloudStorage:
    def __init__(self, url: str, key: str, bucket: str, timeout: int) -> None:
        self.base_url = f"{url.rstrip('/')}/storage/v1"
        self.bucket = bucket
        self.timeout = timeout
        self.session = requests.Session()
        self.session.headers["apikey"] = key
        if key.startswith("eyJ"):
            self.session.headers["Authorization"] = f"Bearer {key}"

    def list_files(self) -> list[str]:
        payload = {"prefix": "", "limit": LIST_LIMIT, "offset": 0, "sortBy": {"column": "created_at", "order": "asc"}}
        entries = self._request("POST", f"/object/list/{self.bucket}", json=payload).json()
        return [entry["name"] for entry in entries if entry.get("id") and is_safe_filename(entry["name"])]

    def download(self, name: str) -> bytes:
        return self._request("GET", f"/object/{self.bucket}/{name}").content

    def delete(self, names: Iterable[str]) -> None:
        self._request("DELETE", f"/object/{self.bucket}", json={"prefixes": list(names)})

    def _request(self, method: str, path: str, **kwargs) -> requests.Response:
        try:
            response = self.session.request(method, f"{self.base_url}{path}", timeout=self.timeout, **kwargs)
        except requests.RequestException as error:
            raise CloudError(str(error)) from error
        if not response.ok:
            raise CloudError(f"{response.status_code} {response.text[:200]}")
        return response


def sync_uploads(cloud: CloudStorage, uploads_dir: Path) -> int:
    downloaded = 0
    stored = []
    try:
        for name in cloud.list_files():
            target = uploads_dir / name
            if not target.exists():
                partial = target.with_name(f"{name}.part")
                partial.write_bytes(cloud.download(name))
                partial.replace(target)
                downloaded += 1
            stored.append(name)
    finally:
        if stored:
            cloud.delete(stored)
    return downloaded
