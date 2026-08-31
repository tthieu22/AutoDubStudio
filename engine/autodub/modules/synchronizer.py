import json
import math
import os
import shutil
import subprocess
import time
import wave
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, Any, List, Optional, Callable, Tuple

from autodub.models.project import Project
from autodub.pipeline.state import PipelineStage, StageStatus, validate_state_transition
from autodub.pipeline.progress import emit_event
from autodub.utils.ffmpeg import FFmpegRunner, find_ffmpeg, find_ffprobe
from autodub.utils.files import atomic_write_json
from autodub.utils.logging import setup_logger
from autodub.exceptions import (
    AutoDubError,
    PipelineCancelledError,
    SyncError,
    SyncInputError,
    SyncTTSMissingError,
    SyncInvalidAudioError,
    SyncFFmpegError,
    SyncDurationMismatchError,
    SyncExtremeSpeedError,
    SyncOverlapError,
    SyncCancelledError,
)

from autodub.modules.sync_utils import (
    MIN_SPEED_FACTOR,
    MAX_SPEED_FACTOR,
    DURATION_TOLERANCE_SECONDS,
    MIN_TARGET_DURATION,
    calculate_target_duration,
    calculate_speed_factor,
    _fmt_speed,
    build_atempo_filter,
    validate_sync_duration,
    probe_audio_duration,
    generate_silent_wav,
    resolve_timeline_overlaps,
)

logger = setup_logger()


@dataclass
class SyncResult:
    completed_segments: int = 0
    skipped_segments: int = 0
    failed_segments: int = 0
    total_segments: int = 0
    total_processing_time: float = 0.0
    max_duration_error: float = 0.0
    average_duration_error: float = 0.0
    clamped_segments: int = 0
    retries_count: int = 0


def resolve_timeline_gaps(segments: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Calculate gaps between consecutive segments in timeline order."""
    sorted_segs = sorted(segments, key=lambda x: float(x.get("effective_start", x.get("start", 0.0))))
    items_with_gaps = []
    prev_end = 0.0

    for seg in sorted_segs:
        start = float(seg.get("effective_start", seg.get("start", 0.0)))
        end = float(seg.get("effective_end", seg.get("end", 0.0)))
        if start > prev_end:
            gap_dur = round(start - prev_end, 3)
            items_with_gaps.append({
                "type": "gap",
                "start": prev_end,
                "end": start,
                "duration": gap_dur
            })
        items_with_gaps.append({
            "type": "segment",
            "segment": seg,
            "start": start,
            "end": end,
            "duration": round(end - start, 3)
        })
        prev_end = max(prev_end, end)

    return items_with_gaps


class RealSynchronizer:
    """Production-quality Audio Synchronization stage runner using FFmpeg atempo."""

    def __init__(self, step_delay: float = 0.05, ffmpeg_runner: Optional[FFmpegRunner] = None):
        self.step_delay = step_delay
        self.runner = ffmpeg_runner or FFmpegRunner()

    def run_segment_sync(
        self,
        input_tts: Path,
        output_synced: Path,
        speed_factor: float,
        target_duration: float,
        tolerance: float = DURATION_TOLERANCE_SECONDS,
        is_cancelled: Optional[Callable[[], bool]] = None
    ) -> Tuple[float, float, int]:
        """Synchronize a single TTS audio file to target duration using atempo filter with 2-pass correction."""
        input_tts = Path(input_tts)
        output_synced = Path(output_synced)
        output_synced.parent.mkdir(parents=True, exist_ok=True)

        tmp_output = output_synced.with_suffix(".tmp")
        if tmp_output.exists():
            try:
                tmp_output.unlink()
            except Exception:
                pass

        # If speed factor is locked to 1.0, bypass atempo correction entirely
        if abs(speed_factor - 1.0) < 1e-4:
            if is_cancelled and is_cancelled():
                raise SyncCancelledError("Sync process cancelled by user.")

            cmd = [
                str(self.runner.ffmpeg_path),
                "-y",
                "-i", str(input_tts),
                "-ac", "1",
                "-c:a", "pcm_s16le",
                "-f", "wav",
                str(tmp_output)
            ]

            process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, encoding="utf-8", errors="replace")
            try:
                while True:
                    if is_cancelled and is_cancelled():
                        process.terminate()
                        try:
                            process.wait(timeout=2)
                        except subprocess.TimeoutExpired:
                            process.kill()
                        raise SyncCancelledError("Sync process cancelled by user.")
                    if process.poll() is not None:
                        break
                    time.sleep(0.01)

                ret_code = process.wait()
                if ret_code != 0:
                    stderr_out = process.stderr.read()
                    raise SyncFFmpegError(f"FFmpeg process failed with exit code {ret_code}: {stderr_out}")
            except Exception:
                if process.poll() is None:
                    process.kill()
                if tmp_output.exists():
                    try:
                        tmp_output.unlink()
                    except Exception:
                        pass
                raise

            actual_duration = probe_audio_duration(tmp_output, self.runner)

            # Pad with silence if shorter than target duration
            if actual_duration < target_duration:
                padded_tmp = output_synced.with_suffix(".padded.tmp")
                pad_cmd = [
                    str(self.runner.ffmpeg_path),
                    "-y",
                    "-i", str(tmp_output),
                    "-filter:a", "apad",
                    "-t", f"{target_duration:.3f}",
                    "-ac", "1",
                    "-c:a", "pcm_s16le",
                    "-f", "wav",
                    str(padded_tmp)
                ]
                pad_proc = subprocess.Popen(pad_cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, encoding="utf-8", errors="replace")
                try:
                    while True:
                        if is_cancelled and is_cancelled():
                            pad_proc.terminate()
                            try:
                                pad_proc.wait(timeout=2)
                            except subprocess.TimeoutExpired:
                                pad_proc.kill()
                            raise SyncCancelledError("Sync process cancelled by user.")
                        if pad_proc.poll() is not None:
                            break
                        time.sleep(0.01)

                    ret_code = pad_proc.wait()
                    if ret_code != 0:
                        stderr_out = pad_proc.stderr.read()
                        raise SyncFFmpegError(f"FFmpeg padding failed with exit code {ret_code}: {stderr_out}")
                except Exception:
                    if pad_proc.poll() is None:
                        pad_proc.kill()
                    if padded_tmp.exists():
                        try:
                            padded_tmp.unlink()
                        except Exception:
                            pass
                    raise

                if tmp_output.exists():
                    try:
                        tmp_output.unlink()
                    except Exception:
                        pass

                os.replace(padded_tmp, output_synced)
                final_dur = target_duration
                err = 0.0
            else:
                os.replace(tmp_output, output_synced)
                final_dur = actual_duration
                err = actual_duration - target_duration

            return final_dur, round(err, 3), 1

        current_speed = speed_factor
        passes_run = 0

        for pass_idx in range(1, 3):
            passes_run = pass_idx
            if is_cancelled and is_cancelled():
                raise SyncCancelledError("Sync process cancelled by user.")

            filter_str = build_atempo_filter(current_speed)
            cmd = [
                str(self.runner.ffmpeg_path),
                "-y",
                "-i", str(input_tts),
            ]
            if filter_str != "anull":
                cmd.extend(["-filter:a", filter_str])
            cmd.extend([
                "-ac", "1",
                "-c:a", "pcm_s16le",
                "-f", "wav",
                str(tmp_output)
            ])

            process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, encoding="utf-8", errors="replace")

            try:
                while True:
                    if is_cancelled and is_cancelled():
                        process.terminate()
                        try:
                            process.wait(timeout=2)
                        except subprocess.TimeoutExpired:
                            process.kill()
                        raise SyncCancelledError("Sync process cancelled by user.")
                    if process.poll() is not None:
                        break
                    time.sleep(0.01)

                ret_code = process.wait()
                if ret_code != 0:
                    stderr_out = process.stderr.read()
                    raise SyncFFmpegError(f"FFmpeg atempo process failed with exit code {ret_code}: {stderr_out}")

            except Exception:
                if process.poll() is None:
                    process.kill()
                if tmp_output.exists():
                    try:
                        tmp_output.unlink()
                    except Exception:
                        pass
                raise

            actual_duration = probe_audio_duration(tmp_output, self.runner)
            err = abs(actual_duration - target_duration)

            if validate_sync_duration(actual_duration, target_duration, tolerance):
                os.replace(tmp_output, output_synced)
                return actual_duration, round(err, 3), passes_run

            if pass_idx == 1:
                if actual_duration > 0:
                    correction_ratio = actual_duration / target_duration
                    current_speed = round(current_speed * correction_ratio, 4)
                    input_tts = tmp_output
                    tmp_output = output_synced.with_suffix(".tmp2")

        if tmp_output.exists():
            os.replace(tmp_output, output_synced)
        elif tmp_output.with_suffix(".tmp2").exists():
            os.replace(tmp_output.with_suffix(".tmp2"), output_synced)

        final_duration = probe_audio_duration(output_synced, self.runner)
        final_err = abs(final_duration - target_duration)

        return final_duration, round(final_err, 3), passes_run

    def generate_combined_audio(
        self,
        project_dir: Path,
        segments_with_gaps: List[Dict[str, Any]],
        output_combined: Path,
        sample_rate: int = 16000
    ) -> float:
        """Generate combined.wav respecting absolute timeline boundaries without loading into RAM."""
        output_combined = Path(output_combined)
        output_combined.parent.mkdir(parents=True, exist_ok=True)
        tmp_combined = output_combined.with_suffix(".tmp")
        if tmp_combined.exists():
            try:
                tmp_combined.unlink()
            except Exception:
                pass

        temp_gaps_dir = project_dir / "audio" / "synced" / ".tmp_gaps"
        temp_gaps_dir.mkdir(parents=True, exist_ok=True)

        concat_list_path = project_dir / "audio" / "synced" / "concat_list.txt"
        concat_lines = []

        # Determine sample rate dynamically from synced files if possible, fallback to sample_rate param
        actual_sample_rate = sample_rate
        for item in segments_with_gaps:
            if item["type"] == "segment":
                seg_id = item["segment"].get("id", 1)
                synced_file = project_dir / "audio" / "synced" / f"{seg_id:06d}.wav"
                if synced_file.exists():
                    try:
                        with wave.open(str(synced_file), "rb") as wf:
                            actual_sample_rate = wf.getframerate()
                            break
                    except Exception:
                        pass

        try:
            gap_idx = 1
            for item in segments_with_gaps:
                if item["type"] == "gap":
                    gap_file = temp_gaps_dir / f"gap_{gap_idx:06d}.wav"
                    generate_silent_wav(gap_file, item["duration"], sample_rate=actual_sample_rate)
                    rel_path = gap_file.relative_to(concat_list_path.parent).as_posix()
                    concat_lines.append(f"file '{rel_path}'")
                    gap_idx += 1
                elif item["type"] == "segment":
                    seg = item["segment"]
                    seg_id = seg.get("id", 1)
                    synced_file = project_dir / "audio" / "synced" / f"{seg_id:06d}.wav"
                    if not synced_file.exists():
                        synced_file = temp_gaps_dir / f"seg_silent_{seg_id:06d}.wav"
                        generate_silent_wav(synced_file, item["duration"], sample_rate=actual_sample_rate)
                    rel_path = synced_file.relative_to(concat_list_path.parent).as_posix()
                    concat_lines.append(f"file '{rel_path}'")

            with open(concat_list_path, "w", encoding="utf-8") as f:
                f.write("\n".join(concat_lines) + "\n")

            cmd = [
                str(self.runner.ffmpeg_path),
                "-y",
                "-f", "concat",
                "-safe", "0",
                "-i", str(concat_list_path),
                "-c:a", "pcm_s16le",
                "-f", "wav",
                str(tmp_combined)
            ]

            res = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, check=True, encoding="utf-8", errors="replace")

            os.replace(tmp_combined, output_combined)
            total_dur = probe_audio_duration(output_combined, self.runner)
            return total_dur

        finally:
            if concat_list_path.exists():
                try:
                    concat_list_path.unlink()
                except Exception:
                    pass
            if temp_gaps_dir.exists():
                shutil.rmtree(temp_gaps_dir, ignore_errors=True)

    def run(
        self,
        project: Project,
        is_cancelled: Optional[Callable[[], bool]] = None,
        fail_at_step: Optional[int] = None,
        force: bool = False,
        speed_min: float = MIN_SPEED_FACTOR,
        speed_max: float = MAX_SPEED_FACTOR,
        tolerance: float = DURATION_TOLERANCE_SECONDS,
        overlap_policy: str = "TRIM",
        extreme_policy: str = "CLAMP"
    ) -> float:
        stage_name = PipelineStage.SYNC.value
        stage_info = project.get_stage_info(stage_name)
        start_time = time.time()

        if stage_info.get("status") == StageStatus.COMPLETED.value and not force:
            emit_event(
                event_type="progress",
                stage=stage_name,
                current=100,
                total=100,
                percent=100.0,
                message="Existing valid Audio Synchronization found."
            )
            emit_event("stage_complete", stage=stage_name, current=100, total=100, percent=100.0)
            return 0.0

        validate_state_transition(stage_info.get("status"), StageStatus.RUNNING, force=force)
        project.update_stage(stage_name, StageStatus.RUNNING.value, current=0, error=None)

        segments = project.data.get("segments", [])
        total_segments = len(segments)

        if total_segments == 0:
            project.update_stage(stage_name, StageStatus.COMPLETED.value, current=0, progress=100)
            emit_event("stage_complete", stage=stage_name, current=0, total=0, percent=100.0)
            return 0.0

        emit_event("stage_start", stage=stage_name, current=0, total=total_segments, percent=0.0)

        resolved_segments = resolve_timeline_overlaps(segments, policy=overlap_policy)

        synced_dir = project.project_dir / "audio" / "synced"
        synced_dir.mkdir(parents=True, exist_ok=True)
        checkpoint_file = synced_dir / "sync.partial.json"

        if force:
            logger.info("Force flag enabled. Cleaning up old synced files.")
            if synced_dir.exists():
                for f in synced_dir.glob("*.wav"):
                    try: f.unlink()
                    except OSError: pass
                for f in synced_dir.glob("*.tmp*"):
                    try: f.unlink()
                    except OSError: pass
            if checkpoint_file.exists():
                try: checkpoint_file.unlink()
                except OSError: pass

        checkpoint = {
            "version": 1,
            "completed_segments": [],
            "segments": {}
        }

        if checkpoint_file.exists() and not force:
            try:
                with open(checkpoint_file, "r", encoding="utf-8") as f:
                    checkpoint = json.load(f)
            except Exception as e:
                logger.warning(f"[SYNC] Corrupted checkpoint found, starting fresh: {e}")

        completed_ids = set(checkpoint.get("completed_segments", []))
        checkpoint_segments = checkpoint.get("segments", {})

        total_audio_duration = 0.0
        clamped_count = 0
        skipped_count = 0
        total_errors = []

        for idx, seg in enumerate(resolved_segments, start=1):
            if is_cancelled and is_cancelled():
                project.update_stage(stage_name, StageStatus.CANCELLED.value, error="Sync stage cancelled by user.")
                emit_event("stage_cancelled", stage=stage_name, current=idx - 1, total=total_segments, error="Sync stage cancelled by user.")
                raise PipelineCancelledError("Sync stage cancelled by user.")

            if fail_at_step is not None and idx == fail_at_step:
                err_msg = f"Simulated error in stage {stage_name} at step {fail_at_step}"
                project.update_stage(stage_name, StageStatus.FAILED.value, current=idx - 1, error=err_msg)
                emit_event("stage_error", stage=stage_name, current=idx - 1, total=total_segments, error=err_msg)
                raise RuntimeError(err_msg)

            seg_id = seg.get("id", idx)
            target_duration = float(seg.get("target_duration", calculate_target_duration(seg)))
            out_wav = synced_dir / f"{seg_id:06d}.wav"

            if not force and str(seg_id) in checkpoint_segments and out_wav.exists() and out_wav.stat().st_size > 0:
                meta_info = checkpoint_segments[str(seg_id)]
                if meta_info.get("status") in ("COMPLETED", "SKIPPED"):
                    out_dur = probe_audio_duration(out_wav, self.runner)
                    if validate_sync_duration(out_dur, target_duration, tolerance) or meta_info.get("status") == "SKIPPED":
                        total_audio_duration += out_dur
                        err = abs(out_dur - target_duration)
                        total_errors.append(err)

                        seg["sync"] = {
                            "path": f"audio/synced/{seg_id:06d}.wav",
                            "target_duration": target_duration,
                            "output_duration": out_dur,
                            "requested_speed": meta_info.get("requested_speed", 1.0),
                            "applied_speed": meta_info.get("applied_speed", 1.0),
                            "error": round(err, 3),
                            "clamped": meta_info.get("clamped", False),
                            "status": meta_info.get("status")
                        }

                        pct = int((idx / total_segments) * 100.0)
                        project.update_stage(stage_name, StageStatus.RUNNING.value, current=idx, progress=pct)
                        emit_event(
                            "progress",
                            stage=stage_name,
                            current=idx,
                            total=total_segments,
                            percent=pct,
                            segment_id=seg_id,
                            target_duration=target_duration,
                            output_duration=out_dur,
                            elapsed=round(time.time() - start_time, 2)
                        )
                        time.sleep(self.step_delay)
                        continue

            if target_duration < MIN_TARGET_DURATION:
                logger.warning(f"[SYNC] Segment {seg_id} target duration ({target_duration}s) < min {MIN_TARGET_DURATION}s. Marking SKIPPED.")
                out_dur = generate_silent_wav(out_wav, max(target_duration, 0.01))
                skipped_count += 1

                seg["sync"] = {
                    "path": f"audio/synced/{seg_id:06d}.wav",
                    "target_duration": target_duration,
                    "output_duration": out_dur,
                    "requested_speed": 1.0,
                    "applied_speed": 1.0,
                    "error": 0.0,
                    "clamped": False,
                    "status": "SKIPPED",
                    "reason": "TARGET_DURATION_TOO_SHORT"
                }

                completed_ids.add(seg_id)
                checkpoint_segments[str(seg_id)] = seg["sync"]
                checkpoint["completed_segments"] = list(completed_ids)
                checkpoint["segments"] = checkpoint_segments
                atomic_write_json(checkpoint_file, checkpoint)

                pct = int((idx / total_segments) * 100.0)
                project.update_stage(stage_name, StageStatus.RUNNING.value, current=idx, progress=pct)
                emit_event(
                    "progress",
                    stage=stage_name,
                    current=idx,
                    total=total_segments,
                    percent=pct,
                    segment_id=seg_id,
                    target_duration=target_duration,
                    output_duration=out_dur,
                    elapsed=round(time.time() - start_time, 2)
                )
                time.sleep(self.step_delay)
                continue

            tts_info = seg.get("tts", {})
            tts_rel_path = tts_info.get("path", f"audio/tts/{seg_id:06d}.wav")
            tts_wav = project.project_dir / tts_rel_path
            tts_status = tts_info.get("status", "")

            if not tts_wav.exists() or tts_status == "SKIPPED" or seg.get("text", "").strip() == "":
                logger.info(f"[SYNC] Segment {seg_id} empty/missing TTS. Generating silent WAV.")
                out_dur = generate_silent_wav(out_wav, target_duration)
                skipped_count += 1

                seg["sync"] = {
                    "path": f"audio/synced/{seg_id:06d}.wav",
                    "target_duration": target_duration,
                    "output_duration": out_dur,
                    "requested_speed": 1.0,
                    "applied_speed": 1.0,
                    "error": 0.0,
                    "clamped": False,
                    "status": "SKIPPED",
                    "reason": "EMPTY_TEXT" if seg.get("text", "").strip() == "" else "MISSING_TTS"
                }

                completed_ids.add(seg_id)
                checkpoint_segments[str(seg_id)] = seg["sync"]
                checkpoint["completed_segments"] = list(completed_ids)
                checkpoint["segments"] = checkpoint_segments
                atomic_write_json(checkpoint_file, checkpoint)

                pct = int((idx / total_segments) * 100.0)
                project.update_stage(stage_name, StageStatus.RUNNING.value, current=idx, progress=pct)
                emit_event(
                    "progress",
                    stage=stage_name,
                    current=idx,
                    total=total_segments,
                    percent=pct,
                    segment_id=seg_id,
                    target_duration=target_duration,
                    output_duration=out_dur,
                    elapsed=round(time.time() - start_time, 2)
                )
                time.sleep(self.step_delay)
                continue

            try:
                tts_duration = float(probe_audio_duration(tts_wav, self.runner))
            except Exception:
                tts_duration = 0.0

            if tts_duration <= 0.0:
                out_dur = generate_silent_wav(out_wav, target_duration)
                skipped_count += 1

                seg["sync"] = {
                    "path": f"audio/synced/{seg_id:06d}.wav",
                    "target_duration": target_duration,
                    "output_duration": out_dur,
                    "requested_speed": 1.0,
                    "applied_speed": 1.0,
                    "error": 0.0,
                    "clamped": False,
                    "status": "SKIPPED",
                    "reason": "ZERO_DURATION_TTS"
                }

                completed_ids.add(seg_id)
                checkpoint_segments[str(seg_id)] = seg["sync"]
                checkpoint["completed_segments"] = list(completed_ids)
                checkpoint["segments"] = checkpoint_segments
                atomic_write_json(checkpoint_file, checkpoint)

                pct = int((idx / total_segments) * 100.0)
                project.update_stage(stage_name, StageStatus.RUNNING.value, current=idx, progress=pct)
                emit_event(
                    "progress",
                    stage=stage_name,
                    current=idx,
                    total=total_segments,
                    percent=pct,
                    segment_id=seg_id,
                    target_duration=target_duration,
                    output_duration=out_dur,
                    elapsed=round(time.time() - start_time, 2)
                )
                time.sleep(self.step_delay)
                continue

            from autodub.modules.narration import NaturalPacingEngine
            pacing_engine = NaturalPacingEngine(min_speed=1.0, max_speed=1.0)
            
            raw_text = seg.get("translation") or seg.get("text") or ""
            applied_speed, expected_dur, trailing_pause_ms, pacing_mode = pacing_engine.evaluate_pacing(
                natural_audio_duration=tts_duration,
                target_available_duration=target_duration,
                text=raw_text
            )
            requested_speed = calculate_speed_factor(tts_duration, target_duration)
            clamped = pacing_mode != "natural"

            retry_count = 0
            last_err = None

            while retry_count < 3:
                try:
                    out_dur, err_sec, passes = self.run_segment_sync(
                        input_tts=tts_wav,
                        output_synced=out_wav,
                        speed_factor=applied_speed,
                        target_duration=target_duration,
                        tolerance=tolerance,
                        is_cancelled=is_cancelled
                    )

                    if not validate_sync_duration(out_dur, target_duration, tolerance) and not clamped:
                        logger.warning(f"[SYNC] Segment {seg_id} output duration ({out_dur}s) differs from target ({target_duration}s) by {err_sec}s. Clamping segment.")
                        clamped = True

                    total_audio_duration += out_dur
                    total_errors.append(err_sec)

                    seg["sync"] = {
                        "path": f"audio/synced/{seg_id:06d}.wav",
                        "target_duration": target_duration,
                        "original_tts_duration": tts_duration,
                        "output_duration": out_dur,
                        "requested_speed": requested_speed,
                        "applied_speed": applied_speed,
                        "error": err_sec,
                        "clamped": clamped,
                        "status": "COMPLETED"
                    }

                    completed_ids.add(seg_id)
                    checkpoint_segments[str(seg_id)] = seg["sync"]
                    checkpoint["completed_segments"] = list(completed_ids)
                    checkpoint["segments"] = checkpoint_segments
                    atomic_write_json(checkpoint_file, checkpoint)

                    logger.info(f"[SYNC] Segment {seg_id} TTS={tts_duration}s Target={target_duration}s Speed={applied_speed}x Out={out_dur}s Error={err_sec}s Status=COMPLETED")
                    break

                except (SyncCancelledError, PipelineCancelledError):
                    raise
                except Exception as e:
                    retry_count += 1
                    last_err = e
                    logger.warning(f"Sync attempt {retry_count}/3 failed for segment {seg_id}: {e}")
                    if retry_count < 3:
                        time.sleep(2 ** (retry_count - 1))

            if retry_count >= 3 and last_err:
                err_msg = f"Sync failed for segment {seg_id} after 3 retries: {last_err}"
                project.update_stage(stage_name, StageStatus.FAILED.value, current=idx - 1, error=err_msg)
                emit_event("stage_error", stage=stage_name, current=idx - 1, total=total_segments, error=err_msg)
                raise SyncError(err_msg)

            pct = int((idx / total_segments) * 100.0)
            project.update_stage(stage_name, StageStatus.RUNNING.value, current=idx, progress=pct)
            emit_event(
                "progress",
                stage=stage_name,
                current=idx,
                total=total_segments,
                percent=pct,
                segment_id=seg_id,
                target_duration=target_duration,
                tts_duration=tts_duration,
                output_duration=out_dur,
                speed_factor=applied_speed,
                elapsed=round(time.time() - start_time, 2)
            )
            time.sleep(self.step_delay)

        items_with_gaps = resolve_timeline_gaps(resolved_segments)
        combined_wav = synced_dir / "combined.wav"
        combined_duration = self.generate_combined_audio(project.project_dir, items_with_gaps, combined_wav)

        # Copy to dubbed_synchronized.wav for frontend editor timeline compatibility
        dubbed_synchronized = project.project_dir / "audio" / "dubbed_synchronized.wav"
        try:
            shutil.copy2(combined_wav, dubbed_synchronized)
            logger.info(f"[SYNC] Copied combined audio to '{dubbed_synchronized}' for editor timeline.")
        except Exception as e:
            logger.warning(f"[SYNC] Failed to copy combined audio to dubbed_synchronized: {e}")

        project.data["segments"] = resolved_segments
        max_err = max(total_errors) if total_errors else 0.0
        avg_err = round(sum(total_errors) / len(total_errors), 4) if total_errors else 0.0

        project.data["sync"] = {
            "total_audio_duration": round(total_audio_duration, 2),
            "combined_audio_duration": round(combined_duration, 2),
            "total_segments": total_segments,
            "clamped_segments": clamped_count,
            "skipped_segments": skipped_count,
            "max_duration_error": max_err,
            "average_duration_error": avg_err,
            "speed_min": speed_min,
            "speed_max": speed_max,
            "tolerance": tolerance,
            "overlap_policy": overlap_policy,
            "extreme_policy": extreme_policy
        }

        project.update_stage(stage_name, StageStatus.COMPLETED.value, current=total_segments, progress=100)
        project.save()

        emit_event("stage_complete", stage=stage_name, current=total_segments, total=total_segments, percent=100.0)
        return round(time.time() - start_time, 2)


class AudioSynchronizer:
    """Public Python API for AutoDubStudio Audio Synchronization."""

    def __init__(self, step_delay: float = 0.05):
        self.step_delay = step_delay

    def synchronize_project(
        self,
        project_dir: Path,
        *,
        force: bool = False,
        speed_min: float = MIN_SPEED_FACTOR,
        speed_max: float = MAX_SPEED_FACTOR,
        tolerance: float = DURATION_TOLERANCE_SECONDS,
        overlap_policy: str = "TRIM",
        extreme_policy: str = "CLAMP"
    ) -> SyncResult:
        project_dir = Path(project_dir)
        project = Project(project_dir)
        runner = RealSynchronizer(step_delay=self.step_delay)

        start_t = time.time()
        elapsed = runner.run(
            project,
            force=force,
            speed_min=speed_min,
            speed_max=speed_max,
            tolerance=tolerance,
            overlap_policy=overlap_policy,
            extreme_policy=extreme_policy
        )

        sync_meta = project.data.get("sync", {})
        return SyncResult(
            completed_segments=project.data.get("sync", {}).get("total_segments", 0) - sync_meta.get("skipped_segments", 0),
            skipped_segments=sync_meta.get("skipped_segments", 0),
            failed_segments=0,
            total_segments=sync_meta.get("total_segments", 0),
            total_processing_time=elapsed,
            max_duration_error=sync_meta.get("max_duration_error", 0.0),
            average_duration_error=sync_meta.get("average_duration_error", 0.0),
            clamped_segments=sync_meta.get("clamped_segments", 0),
            retries_count=0
        )
