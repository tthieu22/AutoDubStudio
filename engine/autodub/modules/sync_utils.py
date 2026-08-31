import os
import wave
import logging
from pathlib import Path
from typing import Dict, Any, List, Optional
from autodub.utils.ffmpeg import FFmpegRunner
from autodub.exceptions import SyncOverlapError

logger = logging.getLogger("autodub")

MIN_SPEED_FACTOR = 0.5
MAX_SPEED_FACTOR = 2.0
DURATION_TOLERANCE_SECONDS = 0.05
MIN_TARGET_DURATION = 0.10


def calculate_target_duration(segment: Dict[str, Any]) -> float:
    """Calculate target duration in seconds for a segment."""
    start = float(segment.get("start", 0.0))
    end = float(segment.get("end", 0.0))
    return max(0.0, round(end - start, 3))


def calculate_speed_factor(tts_duration: float, target_duration: float) -> float:
    """Calculate speed factor ratio (tts_duration / target_duration)."""
    if target_duration <= 0.0:
        return 1.0
    if tts_duration <= 0.0:
        return 1.0
    return round(tts_duration / target_duration, 4)


def _fmt_speed(f: float) -> str:
    s = f"{f:.4f}".rstrip("0").rstrip(".")
    if "." not in s:
        s += ".0"
    return s


def build_atempo_filter(speed_factor: float) -> str:
    """Build FFmpeg filter string for pitch-preserved audio speed modification.
    Chains multiple atempo filters when speed_factor is outside [0.5, 2.0].
    """
    if abs(speed_factor - 1.0) < 1e-4:
        return "anull"

    filters = []
    factor = speed_factor

    if factor > 2.0:
        while factor > 2.0:
            filters.append("atempo=2.0")
            factor /= 2.0
        if abs(factor - 1.0) >= 1e-4:
            filters.append(f"atempo={_fmt_speed(factor)}")
    elif factor < 0.5:
        while factor < 0.5:
            filters.append("atempo=0.5")
            factor /= 0.5
        if abs(factor - 1.0) >= 1e-4:
            filters.append(f"atempo={_fmt_speed(factor)}")
    else:
        filters.append(f"atempo={_fmt_speed(factor)}")

    return ",".join(filters)


def validate_sync_duration(actual: float, target: float, tolerance: float = DURATION_TOLERANCE_SECONDS) -> bool:
    """Check if actual duration is within tolerance of target duration."""
    return abs(actual - target) <= tolerance


def probe_audio_duration(path: Path, runner: Optional[FFmpegRunner] = None) -> float:
    """Probe exact duration of a WAV file in seconds."""
    path = Path(path)
    if not path.exists() or path.stat().st_size == 0:
        return 0.0

    try:
        with wave.open(str(path), "rb") as wf:
            frames = wf.getnframes()
            rate = wf.getframerate()
            if rate > 0:
                return round(frames / float(rate), 3)
    except Exception:
        pass

    if runner is None:
        runner = FFmpegRunner()
    try:
        meta = runner.probe(path)
        return float(meta.get("duration", 0.0))
    except Exception:
        return 0.0


def generate_silent_wav(
    output_path: Path,
    duration: float,
    sample_rate: int = 16000,
    channels: int = 1
) -> float:
    """Generate a silent PCM 16-bit WAV file of specified duration."""
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    num_frames = int(max(0.01, duration) * sample_rate)
    silent_frame = b"\x00\x00" * channels

    tmp_path = output_path.with_suffix(".tmp")
    with wave.open(str(tmp_path), "wb") as wf:
        wf.setnchannels(channels)
        wf.setsampwidth(2)
        wf.setframerate(sample_rate)
        wf.writeframes(silent_frame * num_frames)

    os.replace(tmp_path, output_path)
    return duration


def resolve_timeline_overlaps(segments: List[Dict[str, Any]], policy: str = "TRIM") -> List[Dict[str, Any]]:
    """Detect and resolve subtitle overlaps according to configured policy."""
    sorted_segs = sorted(segments, key=lambda x: float(x.get("start", 0.0)))
    resolved = []
    prev_end = 0.0

    for seg in sorted_segs:
        seg_copy = dict(seg)
        start = float(seg_copy.get("start", 0.0))
        end = float(seg_copy.get("end", 0.0))

        if start < prev_end:
            overlap = round(prev_end - start, 3)
            logger.warning(f"[SYNC][WARNING] Segment {seg_copy.get('id')} overlaps previous end ({prev_end}s) by {overlap}s. Policy: {policy}")

            if policy == "FAIL":
                raise SyncOverlapError(f"Segment {seg_copy.get('id')} start ({start}s) overlaps previous end ({prev_end}s) by {overlap}s under FAIL policy.")
            elif policy == "TRIM":
                effective_start = prev_end
                effective_end = max(effective_start, end)
                seg_copy["effective_start"] = effective_start
                seg_copy["effective_end"] = effective_end
                seg_copy["overlap_trimmed"] = True
                seg_copy["target_duration"] = round(effective_end - effective_start, 3)
                prev_end = effective_end
            elif policy == "SHIFT":
                dur = end - start
                effective_start = prev_end
                effective_end = effective_start + dur
                seg_copy["effective_start"] = effective_start
                seg_copy["effective_end"] = effective_end
                seg_copy["overlap_shifted"] = True
                seg_copy["target_duration"] = round(dur, 3)
                prev_end = effective_end
            elif policy == "ALLOW":
                seg_copy["effective_start"] = start
                seg_copy["effective_end"] = end
                seg_copy["target_duration"] = round(end - start, 3)
                prev_end = max(prev_end, end)
            else:
                seg_copy["effective_start"] = start
                seg_copy["effective_end"] = end
                seg_copy["target_duration"] = round(end - start, 3)
                prev_end = max(prev_end, end)
        else:
            seg_copy["effective_start"] = start
            seg_copy["effective_end"] = end
            seg_copy["target_duration"] = round(end - start, 3)
            prev_end = end

        resolved.append(seg_copy)

    return resolved
