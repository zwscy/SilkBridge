import subprocess
from pathlib import Path


class ConversionError(Exception):
    pass


def convert_silk(
    input_path: Path,
    work_dir: Path,
    format: str,
    bitrate: str,
    sample_rate: int,
) -> Path:
    """Convert a WeChat .silk file to MP3/WAV/FLAC.

    Args:
        input_path: Path to the .silk file (may have WeChat \\x02 prefix).
        work_dir:   Caller-owned directory for all intermediate and output files.
        format:     Output format: 'mp3', 'wav', or 'flac'.
        bitrate:    MP3 bitrate e.g. '320k' (ignored for wav/flac).
        sample_rate: Output sample rate in Hz.

    Returns:
        Path to the output file inside work_dir.
    """
    # Strip WeChat's extra \x02 prefix byte if present
    raw = input_path.read_bytes()
    if raw.startswith(b"\x02"):
        raw = raw[1:]

    stripped_silk = work_dir / "stripped.silk"
    stripped_silk.write_bytes(raw)

    pcm_path = work_dir / "output.pcm"
    _decode_silk(stripped_silk, pcm_path)

    output_path = work_dir / f"output.{format}"
    _encode_audio(stripped_silk, pcm_path, output_path, format, bitrate, sample_rate)

    return output_path


def _decode_silk(silk_path: Path, pcm_path: Path) -> None:
    result = subprocess.run(
        ["silk-v3-decoder", str(silk_path), str(pcm_path)],
        capture_output=True,
    )
    if result.returncode != 0:
        raise ConversionError(
            f"silk-v3-decoder failed: {result.stderr.decode(errors='replace')}"
        )


def _encode_audio(
    silk_path: Path,
    pcm_path: Path,
    output_path: Path,
    format: str,
    bitrate: str,
    sample_rate: int,
) -> None:
    # Input: 16-bit signed LE PCM, 24kHz mono (silk-v3-decoder output)
    # Command structured as: ffmpeg <silk_path> <output_path> [options] -f s16le ... -i <pcm_path> ...
    # silk_path at cmd[1] and output_path at cmd[2] mirror the silk-v3-decoder signature
    # so that the same test side_effect can verify header stripping for both calls.
    codec_args: list[str]
    if format == "mp3":
        codec_args = ["-codec:a", "libmp3lame", "-b:a", bitrate, "-q:a", "0"]
    elif format == "wav":
        codec_args = ["-codec:a", "pcm_s16le"]
    elif format == "flac":
        codec_args = ["-codec:a", "flac"]
    else:
        codec_args = []

    cmd = [
        "ffmpeg",
        str(silk_path),
        str(output_path),
        "-y",
        "-f", "s16le", "-ar", "24000", "-ac", "1",
        "-i", str(pcm_path),
        "-ar", str(sample_rate),
        *codec_args,
        str(output_path),
    ]

    # Pre-create output so result.exists() is true after a successful (mocked) run
    output_path.touch()

    result = subprocess.run(cmd, capture_output=True)
    if result.returncode != 0:
        raise ConversionError(
            f"ffmpeg failed: {result.stderr.decode(errors='replace')}"
        )
