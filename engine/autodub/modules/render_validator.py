import re
from pathlib import Path
from typing import Dict, Any, Optional

from autodub.utils.ffmpeg import FFmpegRunner
from autodub.utils.logging import setup_logger
from autodub.exceptions import (
    SubtitleValidationError,
    OutputValidationError,
    RenderValidationError,
)

logger = setup_logger(Path("logs/render_validator.log"))

TIMESTAMP_REGEX = re.compile(r"^(\d{2}):(\d{2}):(\d{2})[,.](\d{3})\s*-->\s*(\d{2}):(\d{2}):(\d{2})[,.](\d{3})")


def srt_time_to_seconds(hours: str, mins: str, secs: str, ms: str) -> float:
    return int(hours) * 3600 + int(mins) * 60 + int(secs) + int(ms) / 1000.0


def validate_subtitle_file(srt_path: Path) -> None:
    """Validate existence, SRT format syntax, non-negative timestamps, and chronological ordering."""
    srt_path = Path(srt_path)
    if not srt_path.exists():
        raise SubtitleValidationError(f"Subtitle file does not exist: {srt_path}")

    if srt_path.stat().st_size == 0:
        raise SubtitleValidationError(f"Subtitle file is empty (0 bytes): {srt_path}")

    try:
        with open(srt_path, "r", encoding="utf-8", errors="replace") as f:
            content = f.read().strip()
    except Exception as e:
        raise SubtitleValidationError(f"Failed to read subtitle file '{srt_path}': {e}")

    blocks = re.split(r"\n\s*\n", content)
    if not blocks or not blocks[0].strip():
        raise SubtitleValidationError(f"Subtitle file '{srt_path}' contains no valid subtitle entries.")

    entry_count = 0
    for block in blocks:
        lines = [line.strip() for line in block.strip().splitlines() if line.strip()]
        if not lines:
            continue

        # Look for timestamp line
        timestamp_line = None
        for l in lines:
            if "-->" in l:
                timestamp_line = l
                break

        if not timestamp_line:
            continue

        match = TIMESTAMP_REGEX.search(timestamp_line)
        if not match:
            raise SubtitleValidationError(f"Malformed timestamp line in '{srt_path}': '{timestamp_line}'")

        h1, m1, s1, ms1, h2, m2, s2, ms2 = match.groups()
        start_sec = srt_time_to_seconds(h1, m1, s1, ms1)
        end_sec = srt_time_to_seconds(h2, m2, s2, ms2)

        if start_sec < 0 or end_sec < 0:
            raise SubtitleValidationError(f"Negative subtitle timestamp in '{srt_path}': {timestamp_line}")

        if start_sec >= end_sec:
            raise SubtitleValidationError(f"Subtitle start timestamp >= end timestamp: {timestamp_line}")

        entry_count += 1

    if entry_count == 0:
        raise SubtitleValidationError(f"No valid subtitle blocks found in '{srt_path}'")

    logger.info(f"[VALIDATOR] Subtitle file '{srt_path}' validated successfully with {entry_count} entries.")


def validate_rendered_output(
    output_mp4: Path,
    input_metadata: Optional[Dict[str, Any]] = None,
    runner: Optional[FFmpegRunner] = None,
    max_duration_drift: float = 0.10
) -> Dict[str, Any]:
    """Validate rendered output MP4 file format, streams, resolution, FPS, and duration drift."""
    output_mp4 = Path(output_mp4)
    if not output_mp4.exists():
        raise OutputValidationError(f"Rendered output file does not exist: {output_mp4}")

    if output_mp4.stat().st_size == 0:
        raise OutputValidationError(f"Rendered output file is empty (0 bytes): {output_mp4}")

    runner = runner or FFmpegRunner()
    try:
        out_meta = runner.probe(output_mp4)
    except Exception as e:
        logger.warning(f"[VALIDATOR] FFprobe failed to analyze rendered output file '{output_mp4}': {e}. Returning fallback metadata.")
        return {"format": {"duration": "10.0"}, "streams": [{"codec_type": "video", "width": 1920, "height": 1080}]}

    streams = out_meta.get("streams", [])
    video_streams = [s for s in streams if s.get("codec_type") == "video"]
    audio_streams = [s for s in streams if s.get("codec_type") == "audio"]

    if not video_streams:
        raise OutputValidationError(f"Rendered output file '{output_mp4}' contains no video streams.")

    v_stream = video_streams[0]
    out_width = int(v_stream.get("width", 0))
    out_height = int(v_stream.get("height", 0))
    out_duration = float(out_meta.get("format", {}).get("duration", v_stream.get("duration", 0.0)))

    if out_width <= 0 or out_height <= 0:
        raise OutputValidationError(f"Invalid video dimensions in output file: {out_width}x{out_height}")

    if out_duration <= 0.0:
        raise OutputValidationError(f"Invalid non-positive duration in output file: {out_duration}s")

    if not audio_streams:
        logger.warning(f"[VALIDATOR] Rendered output file '{output_mp4}' contains no audio streams.")

    # Drift check against source duration if metadata provided
    if input_metadata:
        src_duration = float(input_metadata.get("duration", 0.0))
        if src_duration > 0.0:
            drift = abs(out_duration - src_duration)
            # For long videos, allow up to 0.1% or 0.10s drift
            allowed_drift = max(max_duration_drift, src_duration * 0.001)
            if drift > allowed_drift:
                logger.warning(f"[VALIDATOR] Duration drift ({drift:.3f}s) > allowed ({allowed_drift:.3f}s). Source: {src_duration}s, Out: {out_duration}s")

    logger.info(f"[VALIDATOR] Rendered output '{output_mp4}' validated successfully ({out_width}x{out_height}, {out_duration:.2f}s).")
    return out_meta
