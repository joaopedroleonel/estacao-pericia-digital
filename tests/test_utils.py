import pytest

from app.utils import dms_to_decimal, is_safe_filename, parse_degree_pair


@pytest.mark.parametrize("name", ["IMG_20260924_1432.jpg", "upload_20261015_143210_a8f3.PNG", "photo-1.webp"])
def test_accepts_safe_filenames(name):
    assert is_safe_filename(name)


@pytest.mark.parametrize("name", ["", "../x.jpg", "a.exe", ".hidden.jpg", "dir/a.jpg", "C:\\a.jpg", "a b.jpg"])
def test_rejects_unsafe_filenames(name):
    assert not is_safe_filename(name)


def test_parses_degree_pair():
    assert parse_degree_pair("-24.5561°, -54.0571°") == (-24.5561, -54.0571)


@pytest.mark.parametrize("text", [None, "", "abc", "-24.5°", "1, 2, 3", "91°, 0°"])
def test_rejects_invalid_degree_pair(text):
    assert parse_degree_pair(text) is None


@pytest.mark.parametrize(("reference", "expected"), [("N", 24.558), ("S", -24.558), ("E", 24.558), ("W", -24.558)])
def test_converts_dms_to_decimal(reference, expected):
    assert dms_to_decimal((24, 33, 28.8), reference) == expected


@pytest.mark.parametrize("values", [None, (1, 2), ("a", 2, 3)])
def test_rejects_incomplete_dms(values):
    assert dms_to_decimal(values, "N") is None
