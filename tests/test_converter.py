import shutil
import tempfile
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from app.converter import ConversionError, convert_silk


def make_work_dir():
    return Path(tempfile.mkdtemp())


def fake_silk():
    return b"\x02#!SILK_V3" + b"\x00" * 100


def _decoder_side_effect(cmd, **kwargs):
    """Create fake output files for subprocess calls; pass through with success."""
    if cmd[0] == "silk-v3-decoder":
        Path(cmd[2]).write_bytes(b"\x00" * 1000)
    elif cmd[0] == "ffmpeg":
        Path(cmd[-1]).write_bytes(b"\x00" * 100)
    return MagicMock(returncode=0)


# ---


def test_convert_to_mp3(tmp_path):
    silk = tmp_path / "input.silk"
    silk.write_bytes(fake_silk())
    work = make_work_dir()
    try:
        with patch("app.converter.subprocess.run") as mock_run:
            mock_run.side_effect = _decoder_side_effect
            result = convert_silk(silk, work_dir=work, format="mp3", bitrate="320k", sample_rate=44100)
        assert result.suffix == ".mp3"
        assert result.exists()
    finally:
        shutil.rmtree(work, ignore_errors=True)


def test_convert_to_wav(tmp_path):
    silk = tmp_path / "input.silk"
    silk.write_bytes(fake_silk())
    work = make_work_dir()
    try:
        with patch("app.converter.subprocess.run") as mock_run:
            mock_run.side_effect = _decoder_side_effect
            result = convert_silk(silk, work_dir=work, format="wav", bitrate="320k", sample_rate=44100)
        assert result.suffix == ".wav"
    finally:
        shutil.rmtree(work, ignore_errors=True)


def test_convert_to_flac(tmp_path):
    silk = tmp_path / "input.silk"
    silk.write_bytes(fake_silk())
    work = make_work_dir()
    try:
        with patch("app.converter.subprocess.run") as mock_run:
            mock_run.side_effect = _decoder_side_effect
            result = convert_silk(silk, work_dir=work, format="flac", bitrate="320k", sample_rate=44100)
        assert result.suffix == ".flac"
    finally:
        shutil.rmtree(work, ignore_errors=True)


def test_strips_wechat_header(tmp_path):
    silk = tmp_path / "input.silk"
    silk.write_bytes(fake_silk())
    work = make_work_dir()
    written_bytes = {}
    try:
        def side_effect(cmd, **kwargs):
            if cmd[0] == "silk-v3-decoder":
                stripped_path = Path(cmd[1])
                written_bytes["content"] = stripped_path.read_bytes()
                Path(cmd[2]).write_bytes(b"\x00" * 100)
            elif cmd[0] == "ffmpeg":
                Path(cmd[-1]).write_bytes(b"\x00" * 100)
            return MagicMock(returncode=0)

        with patch("app.converter.subprocess.run", side_effect=side_effect):
            convert_silk(silk, work_dir=work, format="mp3", bitrate="320k", sample_rate=44100)
    finally:
        shutil.rmtree(work, ignore_errors=True)

    assert written_bytes["content"].startswith(b"#!SILK_V3"), "WeChat \\x02 header not stripped"


def test_decoder_failure_raises(tmp_path):
    silk = tmp_path / "input.silk"
    silk.write_bytes(fake_silk())
    work = make_work_dir()
    try:
        with patch("app.converter.subprocess.run", return_value=MagicMock(returncode=1, stderr=b"err")):
            with pytest.raises(ConversionError, match="silk-v3-decoder failed"):
                convert_silk(silk, work_dir=work, format="mp3", bitrate="320k", sample_rate=44100)
    finally:
        shutil.rmtree(work, ignore_errors=True)


def test_ffmpeg_failure_raises(tmp_path):
    silk = tmp_path / "input.silk"
    silk.write_bytes(fake_silk())
    work = make_work_dir()
    call_count = [0]
    try:
        def side_effect(cmd, **kwargs):
            call_count[0] += 1
            if call_count[0] == 1:
                Path(cmd[2]).write_bytes(b"\x00" * 100)
                return MagicMock(returncode=0)
            return MagicMock(returncode=1, stderr=b"ffmpeg error")

        with patch("app.converter.subprocess.run", side_effect=side_effect):
            with pytest.raises(ConversionError, match="ffmpeg failed"):
                convert_silk(silk, work_dir=work, format="mp3", bitrate="320k", sample_rate=44100)
    finally:
        shutil.rmtree(work, ignore_errors=True)
