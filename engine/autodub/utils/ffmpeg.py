import json
import os
import re
import shutil
import subprocess
import time
from pathlib import Path
from typing import Dict, Any, Optional, Callable

from autodub.config import BASE_DIR, RUNTIME_DIR
from autodub.exceptions import AutoDubError, PipelineCancelledError

def find_ffmpeg() -> Path:
    """Find ffmpeg.exe by configured path, runtime/ffmpeg/, or PATH."""
    local_bin = RUNTIME_DIR / "ffmpeg" / ("ffmpeg.exe" if os.name == "nt" else "ffmpeg")
    if local_bin.exists():
        return local_bin.resolve()
    
    path_bin = shutil.which("ffmpeg")
    if path_bin:
        return Path(path_bin).resolve()
        
    raise AutoDubError("FFmpeg executable not found. Please place ffmpeg.exe inside runtime/ffmpeg/")

def find_ffprobe() -> Path:
    """Find ffprobe.exe by configured path, runtime/ffmpeg/, or PATH."""
    local_bin = RUNTIME_DIR / "ffmpeg" / ("ffprobe.exe" if os.name == "nt" else "ffprobe")
    if local_bin.exists():
        return local_bin.resolve()
    
    path_bin = shutil.which("ffprobe")
    if path_bin:
        return Path(path_bin).resolve()
        
    raise AutoDubError("FFprobe executable not found. Please place ffprobe.exe inside runtime/ffmpeg/")

class FFmpegRunner:
    def __init__(self, ffmpeg_path: Optional[Path] = None, ffprobe_path: Optional[Path] = None):
        self.ffmpeg_path = Path(ffmpeg_path) if ffmpeg_path else find_ffmpeg()
        self.ffprobe_path = Path(ffprobe_path) if ffprobe_path else find_ffprobe()

    def probe(self, input_path: Path) -> Dict[str, Any]:
        """Probe media metadata using ffprobe JSON output."""
        input_path = Path(input_path)
        if not input_path.exists():
            raise AutoDubError(f"Input file not found for probe: {input_path}")

        cmd = [
            str(self.ffprobe_path),
            "-v", "quiet",
            "-print_format", "json",
            "-show_format",
            "-show_streams",
            str(input_path)
        ]

        try:
            res = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, check=True, encoding="utf-8")
            data = json.loads(res.stdout)
        except (subprocess.CalledProcessError, json.JSONDecodeError) as e:
            raise AutoDubError(f"FFprobe failed for file '{input_path}': {e}")

        format_info = data.get("format", {})
        streams = data.get("streams", [])

        video_stream = next((s for s in streams if s.get("codec_type") == "video"), None)
        audio_stream = next((s for s in streams if s.get("codec_type") == "audio"), None)

        duration = float(format_info.get("duration", 0.0))
        if duration == 0.0 and video_stream and "duration" in video_stream:
            duration = float(video_stream["duration"])
        if duration == 0.0 and audio_stream and "duration" in audio_stream:
            duration = float(audio_stream["duration"])

        fps = None
        if video_stream and "r_frame_rate" in video_stream:
            rate_str = video_stream["r_frame_rate"]
            if "/" in rate_str:
                num, den = rate_str.split("/")
                fps = round(float(num) / float(den), 2) if float(den) > 0 else None
            else:
                fps = float(rate_str)

        metadata = {
            "duration": round(duration, 2),
            "format": format_info.get("format_name", "").split(",")[0],
            "video_codec": video_stream.get("codec_name") if video_stream else None,
            "audio_codec": audio_stream.get("codec_name") if audio_stream else None,
            "width": int(video_stream.get("width")) if video_stream and "width" in video_stream else None,
            "height": int(video_stream.get("height")) if video_stream and "height" in video_stream else None,
            "fps": fps,
            "audio_sample_rate": int(audio_stream.get("sample_rate")) if audio_stream and "sample_rate" in audio_stream else None,
            "audio_channels": int(audio_stream.get("channels")) if audio_stream and "channels" in audio_stream else None,
            "has_audio": audio_stream is not None
        }
        return metadata

    def run_extraction(
        self,
        input_video: Path,
        output_audio: Path,
        total_duration: float = 0.0,
        progress_callback: Optional[Callable[[float, float], None]] = None,
        is_cancelled: Optional[Callable[[], bool]] = None
    ) -> float:
        """Run FFmpeg audio extraction to WAV 16kHz mono pcm_s16le with progress tracking."""
        input_video = Path(input_video)
        output_audio = Path(output_audio)
        output_audio.parent.mkdir(parents=True, exist_ok=True)

        cmd = [
            str(self.ffmpeg_path),
            "-y",
            "-i", str(input_video),
            "-map", "0:a:0",
            "-ac", "1",
            "-ar", "16000",
            "-c:a", "pcm_s16le",
            "-f", "wav",
            "-progress", "pipe:1",
            "-nostats",
            str(output_audio)
        ]

        start_time = time.time()
        process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, encoding="utf-8", errors="replace")

        try:
            while True:
                if is_cancelled and is_cancelled():
                    process.terminate()
                    try:
                        process.wait(timeout=2)
                    except subprocess.TimeoutExpired:
                        process.kill()
                    raise PipelineCancelledError("FFmpeg extraction cancelled by user.")

                line = process.stdout.readline()
                if not line and process.poll() is not None:
                    break

                if line:
                    line = line.strip()
                    if line.startswith("out_time_ms="):
                        ms_val = line.split("=")[1]
                        if ms_val.isdigit():
                            current_sec = float(ms_val) / 1000000.0
                            if progress_callback and total_duration > 0:
                                progress_callback(current_sec, total_duration)

            ret_code = process.wait()
            if ret_code != 0:
                stderr_out = process.stderr.read()
                if "Stream map '0:a:0' matches no streams" in stderr_out or "Output file #0 does not contain any stream" in stderr_out:
                    raise AutoDubError("No audio stream found in input video.")
                raise AutoDubError(f"FFmpeg process failed with exit code {ret_code}: {stderr_out}")

        except Exception:
            if process.poll() is None:
                process.kill()
            raise

        return round(time.time() - start_time, 2)

    def validate_wav(self, wav_path: Path) -> Dict[str, Any]:
        """Validate that output WAV file exists and has correct format (16kHz mono pcm_s16le)."""
        wav_path = Path(wav_path)
        if not wav_path.exists() or wav_path.stat().st_size == 0:
            raise AutoDubError(f"Output audio file missing or empty: '{wav_path}'")

        meta = self.probe(wav_path)
        if meta.get("audio_codec") != "pcm_s16le":
            raise AutoDubError(f"Invalid audio codec: expected 'pcm_s16le', got '{meta.get('audio_codec')}'")
        if meta.get("audio_sample_rate") != 16000:
            raise AutoDubError(f"Invalid sample rate: expected 16000, got '{meta.get('audio_sample_rate')}'")
        if meta.get("audio_channels") != 1:
            raise AutoDubError(f"Invalid audio channels: expected 1 (mono), got '{meta.get('audio_channels')}'")

        return meta
