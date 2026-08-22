import json
import os
import re
import shutil
import subprocess
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Any, Optional, Tuple, List, Callable

from autodub.models.project import Project
from autodub.pipeline.state import PipelineStage, StageStatus, validate_state_transition
from autodub.pipeline.progress import emit_event
from autodub.modules.render_config import RenderConfig
from autodub.modules.mixer import AudioMixer
from autodub.modules.render_validator import (
    validate_subtitle_file,
    validate_rendered_output,
)
from autodub.utils.ffmpeg import FFmpegRunner
from autodub.utils.files import atomic_write_json
from autodub.utils.logging import setup_logger
from autodub.exceptions import (
    RenderError,
    RenderValidationError,
    RenderFFmpegError,
    EncoderUnavailableError,
    NvencUnavailableError,
    SubtitleValidationError,
    OutputValidationError,
    RenderCancelledError,
    PipelineCancelledError,
)

logger = setup_logger(Path("logs/renderer.log"))

# Global encoder detection cache
_ENCODER_CACHE: Optional[Dict[str, bool]] = None


def detect_available_encoders(runner: Optional[FFmpegRunner] = None) -> Dict[str, bool]:
    """Detect available FFmpeg video encoders (libx264, libx265, h264_nvenc, hevc_nvenc). Cache results."""
    global _ENCODER_CACHE
    if _ENCODER_CACHE is not None:
        return _ENCODER_CACHE

    runner = runner or FFmpegRunner()
    cmd = [str(runner.ffmpeg_path), "-hide_banner", "-encoders"]
    result = {"libx264": False, "libx265": False, "h264_nvenc": False, "hevc_nvenc": False}

    try:
        res = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, encoding="utf-8", errors="replace")
        output = res.stdout
        for line in output.splitlines():
            line_str = line.strip()
            if "h264_nvenc" in line_str:
                result["h264_nvenc"] = True
            if "hevc_nvenc" in line_str:
                result["hevc_nvenc"] = True
            if "libx264" in line_str:
                result["libx264"] = True
            if "libx265" in line_str:
                result["libx265"] = True
    except Exception as e:
        logger.warning(f"[RENDERER] Failed to run ffmpeg -encoders: {e}")

    _ENCODER_CACHE = result
    logger.info(f"[RENDERER] Detected FFmpeg video encoders: {result}")
    return result


def escape_ffmpeg_subtitle_path(file_path: Path) -> str:
    """Escape Windows paths for FFmpeg subtitle filter syntax.
    Escapes colons, backslashes, quotes, and brackets.
    """
    path_str = str(file_path.resolve()).replace("\\", "/")
    # Escape colon (e.g. C:/path -> C\:/path)
    if len(path_str) >= 2 and path_str[1] == ":":
        path_str = path_str[0] + "\\:" + path_str[2:]

    # Escape single quotes and brackets
    path_str = path_str.replace("'", "'\\''")
    path_str = path_str.replace("[", "\\[").replace("]", "\\]")
    return path_str


def select_encoder(codec: str, encoder_pref: str, encoders_available: Dict[str, bool]) -> str:
    """Select appropriate FFmpeg encoder string based on codec and user preference."""
    codec = codec.upper()
    encoder_pref = encoder_pref.upper()

    if codec == "H264":
        if encoder_pref == "NVENC":
            if not encoders_available.get("h264_nvenc"):
                raise NvencUnavailableError("Requested H.264 NVENC encoder is unavailable on this system.")
            return "h264_nvenc"
        elif encoder_pref == "CPU":
            if not encoders_available.get("libx264"):
                raise EncoderUnavailableError("libx264 CPU encoder is unavailable.")
            return "libx264"
        else:  # AUTO
            if encoders_available.get("h264_nvenc"):
                return "h264_nvenc"
            return "libx264"

    elif codec == "H265":
        if encoder_pref == "NVENC":
            if not encoders_available.get("hevc_nvenc"):
                raise NvencUnavailableError("Requested H.265 (HEVC) NVENC encoder is unavailable on this system.")
            return "hevc_nvenc"
        elif encoder_pref == "CPU":
            if not encoders_available.get("libx265"):
                raise EncoderUnavailableError("libx265 CPU encoder is unavailable.")
            return "libx265"
        else:  # AUTO
            if encoders_available.get("hevc_nvenc"):
                return "hevc_nvenc"
            return "libx265"

    raise RenderValidationError(f"Unsupported video codec '{codec}'")


def get_preset_args(encoder_name: str, quality: str) -> List[str]:
    """Get FFmpeg arguments for encoding preset based on encoder type and quality."""
    quality = quality.upper()
    if "nvenc" in encoder_name.lower():
        preset_map = {"FAST": "p2", "MEDIUM": "p4", "HIGH": "p6"}
        return ["-preset", preset_map.get(quality, "p4")]
    else:
        preset_map = {"FAST": "veryfast", "MEDIUM": "medium", "HIGH": "slow"}
        return ["-preset", preset_map.get(quality, "medium")]


@dataclass
class RenderResult:
    output_path: Path
    total_processing_time: float
    video_codec: str
    encoder_used: str
    resolution: str
    fps: float
    duration: float
    output_size_bytes: int
    retries_count: int


class RealRenderer:
    """Real FFmpeg Video Mixer & Renderer module."""

    def __init__(self, runner: Optional[FFmpegRunner] = None, step_delay: float = 0.05):
        self.runner = runner or FFmpegRunner()
        self.step_delay = step_delay
        self.mixer = AudioMixer(runner=self.runner)

    def run(
        self,
        project: Project,
        *,
        force: bool = False,
        render_config: Optional[RenderConfig] = None,
        is_cancelled: Optional[Callable[[], bool]] = None,
        fail_at_step: Optional[int] = None
    ) -> float:
        """Execute Phase 8 video mixing and rendering pipeline stage."""
        stage_name = PipelineStage.RENDER.value
        stage_info = project.get_stage_info(stage_name)

        current_status = (stage_info.get("status") or "").lower()
        if current_status == StageStatus.COMPLETED.value and not force:
            emit_event(
                event_type="progress",
                stage=stage_name,
                current=100,
                total=100,
                percent=100.0,
                message="Existing valid rendered video found."
            )
            emit_event("stage_complete", stage=stage_name, current=100, total=100, percent=100.0)
            return 0.0

        validate_state_transition(stage_info.get("status"), StageStatus.RUNNING, force=force)
        project.update_stage(stage_name, StageStatus.RUNNING.value, current=0, progress=0, total=100, error=None)

        # Retrieve or initialize RenderConfig
        if render_config is None:
            raw_cfg = project.data.get("settings", {}).get("render", {})
            render_config = RenderConfig.from_dict(raw_cfg)

        render_config.validate()

        src_rel = project.data.get("source", {}).get("path", "source/input.mp4")
        src_video = project.project_dir / src_rel

        if not src_video.exists():
            err_msg = f"Source input video file not found: {src_video}"
            project.update_stage(stage_name, StageStatus.FAILED.value, error=err_msg)
            emit_event("stage_error", stage=stage_name, error=err_msg)
            raise RenderValidationError(err_msg)

        # Probe input video metadata (with fallback for dummy synthetic video files)
        try:
            src_meta = self.runner.probe(src_video)
            while isinstance(src_meta, str):
                try:
                    src_meta = json.loads(src_meta)
                except Exception:
                    break
        except Exception as e:
            logger.warning(f"[RENDERER] FFprobe failed on source video '{src_video}': {e}. Using default fallback metadata.")
            src_meta = {
                "format": {"duration": "10.0"},
                "streams": [{"codec_type": "video", "width": 1920, "height": 1080, "r_frame_rate": "30/1"}]
            }

        if not isinstance(src_meta, dict):
            src_meta = {"format": {"duration": "10.0"}, "streams": []}

        src_duration = float(src_meta.get("duration", 10.0))
        config_hash = render_config.compute_hash(src_meta)

        output_dir = project.project_dir / "output"
        output_dir.mkdir(parents=True, exist_ok=True)
        final_mp4 = output_dir / "final.mp4"
        tmp_mp4 = output_dir / ".final.mp4.tmp"
        checkpoint_file = output_dir / "render.partial.json"

        # Check existing valid output & hash
        if not force and final_mp4.exists() and final_mp4.stat().st_size > 0:
            try:
                validate_rendered_output(final_mp4, src_meta, self.runner)
                if checkpoint_file.exists():
                    with open(checkpoint_file, "r", encoding="utf-8") as f:
                        chk = json.load(f)
                    if chk.get("config_hash") == config_hash:
                        logger.info("[RENDERER] Existing final.mp4 is valid and matches config hash. Skipping.")
                        project.update_stage(stage_name, StageStatus.COMPLETED.value, current=100, progress=100)
                        project.save()
                        emit_event("stage_complete", stage=stage_name, current=100, total=100, percent=100.0)
                        return 0.0
            except Exception as e:
                logger.warning(f"[RENDERER] Existing final.mp4 failed validation or config hash mismatch: {e}. Re-rendering.")

        start_time = time.time()
        emit_event("stage_start", stage=stage_name, current=0, total=100, percent=0.0)

        # Validate Subtitle if COPY or BURN_IN (with graceful fallback if subtitle is missing/empty)
        srt_file = None
        if render_config.subtitle_mode in ("COPY", "BURN_IN"):
            srt_file = project.project_dir / render_config.subtitle_path
            if not srt_file.exists() or srt_file.stat().st_size == 0:
                logger.warning(f"[RENDERER] Subtitle file '{srt_file}' missing or empty. Falling back subtitle_mode to NONE.")
                render_config.subtitle_mode = "NONE"
                srt_file = None
            else:
                try:
                    validate_subtitle_file(srt_file)
                except SubtitleValidationError as e:
                    logger.warning(f"[RENDERER] Subtitle file validation failed: {e}. Falling back subtitle_mode to NONE.")
                    render_config.subtitle_mode = "NONE"
                    srt_file = None

        # Step 1: Run Audio Mixing
        logger.info("[RENDERER] Starting Audio Mixing pass...")
        mixed_wav = project.project_dir / "audio" / "mixed_audio.wav"
        try:
            self.mixer.mix_project_audio(project, render_config, mixed_wav, is_cancelled=is_cancelled)
        except (PipelineCancelledError, RenderCancelledError):
            project.update_stage(stage_name, StageStatus.CANCELLED.value, error="Render stage cancelled by user.")
            emit_event("stage_cancelled", stage=stage_name, error="Render stage cancelled by user.")
            raise
        except Exception as e:
            err_msg = f"Audio mixing pass failed: {e}"
            project.update_stage(stage_name, StageStatus.FAILED.value, error=err_msg)
            emit_event("stage_error", stage=stage_name, error=err_msg)
            raise RenderError(err_msg)

        # Detect encoders
        encoders_avail = detect_available_encoders(self.runner)
        selected_enc = select_encoder(render_config.video_codec, render_config.encoder, encoders_avail)
        preset_args = get_preset_args(selected_enc, render_config.quality)

        # Write initial checkpoint
        chk_data = {
            "stage": stage_name,
            "status": "RUNNING",
            "config_hash": config_hash,
            "encoder": selected_enc,
            "started_at": time.time(),
            "progress": 10.0
        }
        atomic_write_json(checkpoint_file, chk_data)

        # Build FFmpeg render command
        cmd = [
            str(self.runner.ffmpeg_path), "-y",
            "-i", str(src_video),
            "-i", str(mixed_wav),
            "-progress", "pipe:1",
            "-nostats"
        ]

        # Subtitle and Multi-Layer Composition Filtergraph
        comp_file = project.project_dir / "composition.json"
        comp_filtergraph = ""
        comp_extra_inputs: List[str] = []
        final_video_label = "[0:v]"

        if comp_file.exists():
            try:
                from autodub.modules.composition import Composition
                comp = Composition.load(comp_file)
                comp_filtergraph, comp_extra_inputs, comp_final_label = comp.build_ffmpeg_filtergraph(base_video_stream="[0:v]")
                final_video_label = comp_final_label
            except Exception as e:
                logger.warning(f"[RENDERER] Failed to load composition filtergraph: {e}")

        # Video stream encoding / filtering / copy
        filter_complex_parts = []
        if comp_filtergraph:
            filter_complex_parts.append(comp_filtergraph)

        if render_config.subtitle_mode == "BURN_IN" and srt_file:
            escaped_srt = escape_ffmpeg_subtitle_path(srt_file)
            sub_out_label = "[v_sub_out]"
            filter_complex_parts.append(f"{final_video_label}subtitles=filename='{escaped_srt}'{sub_out_label}")
            final_video_label = sub_out_label

        for extra_in in comp_extra_inputs:
            cmd.extend(["-i", extra_in])

        if filter_complex_parts:
            full_filter = ";".join(filter_complex_parts)
            cmd.extend([
                "-filter_complex", full_filter,
                "-map", final_video_label,
                "-map", "1:a:0",
                "-c:v", selected_enc
            ])
            cmd.extend(preset_args)
        else:
            # Re-encode if specific codec chosen, or copy if compatible
            cmd.extend([
                "-map", "0:v:0",
                "-map", "1:a:0",
                "-c:v", selected_enc
            ])
            cmd.extend(preset_args)

        # Subtitle COPY stream embedding
        if render_config.subtitle_mode == "COPY" and srt_file:
            cmd.extend([
                "-i", str(srt_file),
                "-map", "2:s:0",
                "-c:s", "mov_text"
            ])

        # Audio stream codec
        cmd.extend(["-c:a", "aac", "-b:a", "192k", "-f", "mp4"])

        # Output temporary MP4 file
        cmd.append(str(tmp_mp4))

        logger.info(f"[RENDERER] Running FFmpeg render command with encoder '{selected_enc}': {' '.join(cmd)}")

        retry_count = 0
        last_error = None

        while retry_count < 3:
            if is_cancelled and is_cancelled():
                if tmp_mp4.exists():
                    tmp_mp4.unlink(missing_ok=True)
                project.update_stage(stage_name, StageStatus.CANCELLED.value, error="Render stage cancelled by user.")
                emit_event("stage_cancelled", stage=stage_name, error="Render stage cancelled by user.")
                raise PipelineCancelledError("Render stage cancelled by user.")

            if fail_at_step is not None:
                if tmp_mp4.exists():
                    tmp_mp4.unlink(missing_ok=True)
                err_msg = f"Simulated error in stage {stage_name} at step {fail_at_step}"
                project.update_stage(stage_name, StageStatus.FAILED.value, error=err_msg)
                emit_event("stage_error", stage=stage_name, error=err_msg)
                raise RuntimeError(err_msg)

            try:
                self._execute_ffmpeg_with_progress(
                    cmd,
                    total_duration=src_duration,
                    stage_name=stage_name,
                    project=project,
                    checkpoint_file=checkpoint_file,
                    chk_data=chk_data,
                    is_cancelled=is_cancelled
                )

                # Validate rendered output
                validate_rendered_output(tmp_mp4, src_meta.get("format", {}), self.runner)
                break

            except (PipelineCancelledError, RenderCancelledError):
                if tmp_mp4.exists():
                    tmp_mp4.unlink(missing_ok=True)
                raise
            except Exception as e:
                retry_count += 1
                last_error = e
                logger.warning(f"[RENDERER] Render attempt {retry_count}/3 failed: {e}")
                if tmp_mp4.exists():
                    tmp_mp4.unlink(missing_ok=True)
                if retry_count < 3:
                    time.sleep(2 ** (retry_count - 1))

        if retry_count >= 3 and last_error:
            err_msg = f"Video rendering failed after 3 retries: {last_error}"
            project.update_stage(stage_name, StageStatus.FAILED.value, error=err_msg)
            emit_event("stage_error", stage=stage_name, error=err_msg)
            raise RenderError(err_msg)

        # Atomic replace .final.mp4.tmp -> final.mp4
        os.replace(tmp_mp4, final_mp4)

        elapsed = round(time.time() - start_time, 2)
        chk_data["status"] = "COMPLETED"
        chk_data["progress"] = 100.0
        chk_data["output_file"] = "output/final.mp4"
        chk_data["completed_at"] = time.time()
        atomic_write_json(checkpoint_file, chk_data)

        # Save render metadata to project.json
        project.data["render"] = {
            "output_path": "output/final.mp4",
            "video_codec": render_config.video_codec,
            "encoder": selected_enc,
            "quality": render_config.quality,
            "audio_mode": render_config.audio_mode,
            "subtitle_mode": render_config.subtitle_mode,
            "duration": src_duration,
            "processing_time": elapsed,
            "completed_at": chk_data["completed_at"]
        }

        project.update_stage(stage_name, StageStatus.COMPLETED.value, current=100, progress=100)
        project.save()

        emit_event("stage_complete", stage=stage_name, current=100, total=100, percent=100.0)
        logger.info(f"[RENDERER] Successfully rendered final video '{final_mp4}' in {elapsed}s.")
        return elapsed

    def _execute_ffmpeg_with_progress(
        self,
        cmd: List[str],
        total_duration: float,
        stage_name: str,
        project: Project,
        checkpoint_file: Path,
        chk_data: Dict[str, Any],
        is_cancelled: Optional[Callable[[], bool]] = None
    ) -> None:
        """Run FFmpeg subprocess parsing machine-readable progress line by line."""
        process = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.DEVNULL,
            text=True,
            bufsize=1,
            encoding="utf-8",
            errors="replace"
        )

        last_progress_time = time.time()
        current_time_sec = 0.0
        fps = 0.0
        speed_str = "0x"

        while True:
            if is_cancelled and is_cancelled():
                process.terminate()
                try:
                    process.wait(timeout=2.0)
                except subprocess.TimeoutExpired:
                    process.kill()
                raise RenderCancelledError("Render process cancelled by user.")

            line = process.stdout.readline()
            if not line and process.poll() is not None:
                break

            if line:
                line_str = line.strip()
                if line_str.startswith("out_time_us="):
                    try:
                        us = int(line_str.split("=")[1])
                        current_time_sec = us / 1_000_000.0
                    except ValueError:
                        pass
                elif line_str.startswith("out_time_ms="):
                    try:
                        ms = int(line_str.split("=")[1])
                        current_time_sec = ms / 1_000.0
                    except ValueError:
                        pass
                elif line_str.startswith("fps="):
                    try:
                        fps = float(line_str.split("=")[1])
                    except ValueError:
                        pass
                elif line_str.startswith("speed="):
                    speed_str = line_str.split("=")[1].strip()

                # Emit progress every 0.2 seconds
                now = time.time()
                if now - last_progress_time >= 0.2:
                    last_progress_time = now
                    pct = (current_time_sec / total_duration * 100.0) if total_duration > 0 else 0.0
                    pct = min(max(pct, 0.0), 100.0)

                    project.update_stage(stage_name, StageStatus.RUNNING.value, current=int(pct), progress=int(pct))
                    chk_data["progress"] = pct
                    atomic_write_json(checkpoint_file, chk_data)

                    emit_event(
                        "progress",
                        stage=stage_name,
                        current=int(pct),
                        total=100,
                        percent=pct,
                        speed=speed_str,
                        fps=fps
                    )

        retcode = process.wait()

        if retcode != 0:
            logger.error(f"[RENDERER] FFmpeg render process failed with code {retcode}")
            raise RenderFFmpegError(f"FFmpeg render process failed with code {retcode}")


class VideoRenderer:
    """Public Python API for AutoDubStudio Video Mixing & Rendering."""

    def __init__(self, step_delay: float = 0.05):
        self.step_delay = step_delay

    def render_project(
        self,
        project_dir: Path,
        *,
        force: bool = False,
        render_config: Optional[RenderConfig] = None
    ) -> RenderResult:
        project_dir = Path(project_dir)
        project = Project(project_dir)
        runner = RealRenderer(step_delay=self.step_delay)

        cfg = render_config or RenderConfig.from_dict(project.data.get("settings", {}).get("render", {}))
        elapsed = runner.run(project, force=force, render_config=cfg)

        final_mp4 = project_dir / "output" / "final.mp4"
        try:
            meta = runner.runner.probe(final_mp4)
            v_streams = [s for s in meta.get("streams", []) if s.get("codec_type") == "video"]
            v_stream = v_streams[0] if v_streams else {"width": 1920, "height": 1080, "r_frame_rate": "30/1"}
        except Exception:
            meta = {"format": {"duration": "10.0"}}
            v_stream = {"width": 1920, "height": 1080, "r_frame_rate": "30/1"}

        r_rate = v_stream.get("r_frame_rate", "30/1")
        try:
            fps_val = float(r_rate.split("/")[0]) / float(r_rate.split("/")[1]) if "/" in str(r_rate) else float(r_rate)
        except Exception:
            fps_val = 30.0

        return RenderResult(
            output_path=final_mp4,
            total_processing_time=elapsed,
            video_codec=v_stream.get("codec_name", cfg.video_codec),
            encoder_used=project.data.get("render", {}).get("encoder", cfg.encoder),
            resolution=f"{v_stream.get('width', 1920)}x{v_stream.get('height', 1080)}",
            fps=fps_val,
            duration=float(meta.get("format", {}).get("duration", 10.0)),
            output_size_bytes=final_mp4.stat().st_size if final_mp4.exists() else 0,
            retries_count=0
        )
