import subprocess
from pathlib import Path

_SILK_PCM_SAMPLE_RATE = 24000
_SILK_PCM_CHANNELS = 1


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
    _encode_audio(pcm_path, output_path, format, bitrate, sample_rate)

    return output_path


def convert_mp3_to_silk(input_path: Path, work_dir: Path) -> Path:
    """Convert an MP3 file to a WeChat-compatible .silk file."""
    pcm_path = work_dir / "input.pcm"
    _decode_audio_to_pcm(input_path, pcm_path)

    output_path = work_dir / "output.silk"
    _encode_silk(pcm_path, output_path)

    return output_path


def _decode_silk(silk_path: Path, pcm_path: Path) -> None:
    try:
        result = subprocess.run(
            ["silk-v3-decoder", str(silk_path), str(pcm_path)],
            capture_output=True,
        )
    except FileNotFoundError:
        raise ConversionError("silk-v3-decoder not found; is it installed and on PATH?")
    if result.returncode != 0:
        raise ConversionError(
            f"silk-v3-decoder failed: {result.stderr.decode(errors='replace')}"
        )


def _decode_audio_to_pcm(input_path: Path, pcm_path: Path) -> None:
    cmd = [
        "ffmpeg", "-y",
        "-i", str(input_path),
        "-f", "s16le",
        "-ar", str(_SILK_PCM_SAMPLE_RATE),
        "-ac", str(_SILK_PCM_CHANNELS),
        str(pcm_path),
    ]

    try:
        result = subprocess.run(cmd, capture_output=True)
    except FileNotFoundError:
        raise ConversionError("ffmpeg not found; is it installed and on PATH?")
    if result.returncode != 0:
        raise ConversionError(
            f"ffmpeg failed: {result.stderr.decode(errors='replace')}"
        )


def _encode_audio(
    pcm_path: Path, output_path: Path, format: str, bitrate: str, sample_rate: int
) -> None:
    # Input: 16-bit signed LE PCM, 24kHz mono (silk-v3-decoder output)
    cmd = [
        "ffmpeg", "-y",
        "-f", "s16le", "-ar", str(_SILK_PCM_SAMPLE_RATE), "-ac", str(_SILK_PCM_CHANNELS),
        "-i", str(pcm_path),
        "-ar", str(sample_rate),
    ]

    if format == "mp3":
        cmd += ["-codec:a", "libmp3lame", "-b:a", bitrate]
    elif format == "wav":
        cmd += ["-codec:a", "pcm_s16le"]
    elif format == "flac":
        cmd += ["-codec:a", "flac"]
    else:
        raise ConversionError(f"Unsupported format: {format!r}. Expected mp3, wav, or flac.")

    cmd.append(str(output_path))

    try:
        result = subprocess.run(cmd, capture_output=True)
    except FileNotFoundError:
        raise ConversionError("ffmpeg not found; is it installed and on PATH?")
    if result.returncode != 0:
        raise ConversionError(
            f"ffmpeg failed: {result.stderr.decode(errors='replace')}"
        )


def _encode_silk(pcm_path: Path, output_path: Path) -> None:
    try:
        result = subprocess.run(
            ["silk-v3-encoder", str(pcm_path), str(output_path), "-tencent"],
            capture_output=True,
        )
    except FileNotFoundError:
        raise ConversionError("silk-v3-encoder not found; is it installed and on PATH?")
    if result.returncode != 0:
        raise ConversionError(
            f"silk-v3-encoder failed: {result.stderr.decode(errors='replace')}"
        )
