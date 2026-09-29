from __future__ import annotations

import subprocess
from pathlib import Path

from app.utils import is_safe_filename


DEVICE_PROPERTIES = {
    "manufacturer": "ro.product.manufacturer",
    "model": "ro.product.model",
    "androidVersion": "ro.build.version.release",
}


class AdbError(Exception):
    def __init__(self, code: str) -> None:
        super().__init__(code)
        self.code = code


class AdbService:
    def __init__(self, adb_path: str, timeout: int, camera_dir: str) -> None:
        self.adb_path = adb_path
        self.timeout = timeout
        self.camera_dir = camera_dir

    def get_device_info(self) -> dict[str, str]:
        self._ensure_device()
        return {key: self._run("shell", "getprop", prop).strip() for key, prop in DEVICE_PROPERTIES.items()}

    def list_camera_photos(self, limit: int) -> list[str]:
        self._ensure_device()
        names = (line.strip() for line in self._run("shell", "ls", "-t", self.camera_dir).splitlines())
        return [name for name in names if is_safe_filename(name)][:limit]

    def pull_photo(self, name: str, destination: Path) -> Path:
        self._ensure_device()
        target = destination / name
        self._run("pull", f"{self.camera_dir}/{name}", str(target))
        return target

    def _ensure_device(self) -> None:
        states = [line.split()[-1] for line in self._run("devices").splitlines()[1:] if line.strip()]
        if "device" in states:
            return
        raise AdbError("unauthorized" if "unauthorized" in states else "no_device")

    def _run(self, *args: str) -> str:
        try:
            result = subprocess.run(
                [self.adb_path, *args],
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="replace",
                timeout=self.timeout,
                check=False,
            )
        except FileNotFoundError as error:
            raise AdbError("adb_not_found") from error
        except subprocess.TimeoutExpired as error:
            raise AdbError("timeout") from error
        if result.returncode != 0:
            raise AdbError(_classify_failure(result.stderr + result.stdout))
        return result.stdout


def _classify_failure(message: str) -> str:
    lowered = message.lower()
    if "unauthorized" in lowered:
        return "unauthorized"
    if "no such file" in lowered or "does not exist" in lowered:
        return "file_not_found"
    if "no devices" in lowered or ("device" in lowered and "not found" in lowered):
        return "no_device"
    return "command_failed"
