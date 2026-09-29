from __future__ import annotations

import ctypes
import subprocess
import sys
import time
from ctypes import wintypes


WINDOW_TITLE = "Celular"

WINDOW_X = 41

WINDOW_Y = 80

WINDOW_HEIGHT = 950

CORNER_RADIUS = 15

WINDOW_WAIT_SECONDS = 20

POLL_INTERVAL_SECONDS = 0.3

SCRCPY_COMMAND = [
    "scrcpy",
    "--window-borderless",
    "--always-on-top",
    f"--window-x={WINDOW_X}",
    f"--window-y={WINDOW_Y}",
    f"--window-height={WINDOW_HEIGHT}",
    "--no-audio",
    "--stay-awake",
    "--show-touches",
    "-K",
    "-M",
    f"--window-title={WINDOW_TITLE}",
]

user32 = ctypes.WinDLL("user32")

gdi32 = ctypes.WinDLL("gdi32")

user32.SetProcessDPIAware.restype = wintypes.BOOL
user32.FindWindowW.argtypes = [wintypes.LPCWSTR, wintypes.LPCWSTR]
user32.FindWindowW.restype = wintypes.HWND
user32.GetWindowRect.argtypes = [wintypes.HWND, ctypes.POINTER(wintypes.RECT)]
user32.GetWindowRect.restype = wintypes.BOOL
user32.SetWindowRgn.argtypes = [wintypes.HWND, wintypes.HRGN, wintypes.BOOL]
user32.SetWindowRgn.restype = ctypes.c_int
gdi32.CreateRoundRectRgn.argtypes = [ctypes.c_int] * 6
gdi32.CreateRoundRectRgn.restype = wintypes.HRGN
gdi32.DeleteObject.argtypes = [wintypes.HGDIOBJ]
gdi32.DeleteObject.restype = wintypes.BOOL


def main() -> int:
    user32.SetProcessDPIAware()
    process = subprocess.Popen(SCRCPY_COMMAND)
    try:
        window = wait_for_window(process)
        if window:
            keep_corners_rounded(window, process)
        return process.wait()
    except KeyboardInterrupt:
        process.terminate()
        return process.wait()


def wait_for_window(process: subprocess.Popen) -> int | None:
    deadline = time.monotonic() + WINDOW_WAIT_SECONDS
    while time.monotonic() < deadline and process.poll() is None:
        window = user32.FindWindowW(None, WINDOW_TITLE)
        if window:
            return window
        time.sleep(POLL_INTERVAL_SECONDS)
    return None


def keep_corners_rounded(window: int, process: subprocess.Popen) -> None:
    rounded_size = None
    while process.poll() is None:
        size = window_size(window)
        if size and size != rounded_size:
            round_corners(window, *size)
            rounded_size = size
        time.sleep(POLL_INTERVAL_SECONDS)


def window_size(window: int) -> tuple[int, int] | None:
    rect = wintypes.RECT()
    if not user32.GetWindowRect(window, ctypes.byref(rect)):
        return None
    width, height = rect.right - rect.left, rect.bottom - rect.top
    return (width, height) if width > 0 and height > 0 else None


def round_corners(window: int, width: int, height: int) -> None:
    diameter = CORNER_RADIUS * 2
    region = gdi32.CreateRoundRectRgn(0, 0, width + 1, height + 1, diameter, diameter)
    if not user32.SetWindowRgn(window, region, True):
        gdi32.DeleteObject(region)


if __name__ == "__main__":
    sys.exit(main())
