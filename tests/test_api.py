import shutil
from pathlib import Path
from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient

FIXTURE = Path(__file__).parent / "fixtures" / "sample.silk"


def get_client():
    from app.main import app
    return TestClient(app)


def test_health_check():
    client = get_client()
    resp = client.get("/health")
    assert resp.status_code == 200
    assert resp.json() == {"status": "ok"}


def test_convert_mp3_default(tmp_path):
    fake_out = tmp_path / "output.mp3"
    fake_out.write_bytes(b"ID3fake")

    with patch("app.main.convert_silk", return_value=fake_out) as mock_conv:
        client = get_client()
        with open(FIXTURE, "rb") as f:
            resp = client.post("/convert", files={"file": ("v.silk", f, "application/octet-stream")})

    assert resp.status_code == 200
    assert resp.content == b"ID3fake"
    assert "audio/mpeg" in resp.headers["content-type"]
    _, kwargs = mock_conv.call_args
    assert kwargs["format"] == "mp3"
    assert kwargs["bitrate"] == "320k"
    assert kwargs["sample_rate"] == 44100


def test_convert_wav(tmp_path):
    fake_out = tmp_path / "output.wav"
    fake_out.write_bytes(b"RIFF")

    with patch("app.main.convert_silk", return_value=fake_out):
        client = get_client()
        with open(FIXTURE, "rb") as f:
            resp = client.post(
                "/convert",
                files={"file": ("v.silk", f, "application/octet-stream")},
                data={"format": "wav"},
            )

    assert resp.status_code == 200
    assert resp.headers["content-type"].startswith("audio/wav")


def test_convert_flac(tmp_path):
    fake_out = tmp_path / "output.flac"
    fake_out.write_bytes(b"fLaC")

    with patch("app.main.convert_silk", return_value=fake_out):
        client = get_client()
        with open(FIXTURE, "rb") as f:
            resp = client.post(
                "/convert",
                files={"file": ("v.silk", f, "application/octet-stream")},
                data={"format": "flac"},
            )

    assert resp.status_code == 200
    assert "audio/flac" in resp.headers["content-type"]


def test_invalid_format_returns_422():
    client = get_client()
    with open(FIXTURE, "rb") as f:
        resp = client.post(
            "/convert",
            files={"file": ("v.silk", f, "application/octet-stream")},
            data={"format": "ogg"},
        )
    assert resp.status_code == 422


def test_conversion_error_returns_500():
    from app.converter import ConversionError

    with patch("app.main.convert_silk", side_effect=ConversionError("decode failed")):
        client = get_client()
        with open(FIXTURE, "rb") as f:
            resp = client.post("/convert", files={"file": ("v.silk", f, "application/octet-stream")})

    assert resp.status_code == 500
    assert "decode failed" in resp.json()["detail"]
