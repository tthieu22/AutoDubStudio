import os
import sys
import time
import json
import wave
import math
import shutil
import subprocess
from pathlib import Path
from typing import Optional, Dict, List, Tuple, Callable, Any

from autodub.config import BASE_DIR, RUNTIME_DIR, MODELS_DIR
from autodub.models.project import Project
from autodub.pipeline.state import PipelineStage, StageStatus
from autodub.pipeline.progress import emit_event
from autodub.utils.logging import setup_logger
from autodub.exceptions import (
    AutoDubError,
    PiperUnavailableError,
    PiperVoiceNotFoundError,
    PiperSynthesisError,
    PiperInvalidOutputError,
    PiperTimeoutError,
    TTSSynthesisFailedError,
    PipelineCancelledError
)

logger = setup_logger()


class PiperClient:
    """Wrapper around local Piper TTS binary and voice models."""

    def __init__(self, executable_path: Optional[Path] = None, voices_dir: Optional[Path] = None):
        self.executable_path = executable_path or self.find_executable()
        self.voices_dir = voices_dir or (RUNTIME_DIR / "piper" / "voices")

    def find_executable(self) -> Optional[Path]:
        """Locate Piper binary in runtime/piper/ or system PATH."""
        candidates = [
            RUNTIME_DIR / "piper" / "piper.exe",
            RUNTIME_DIR / "piper" / "piper",
            RUNTIME_DIR / "piper.exe",
        ]
        for candidate in candidates:
            if candidate.exists():
                return candidate.resolve()

        which_path = shutil.which("piper")
        if which_path:
            return Path(which_path).resolve()

        return None

    def find_voice(self, voice_name: str) -> Tuple[Optional[Path], Optional[Path]]:
        """
        Locate .onnx and .onnx.json for given voice model name or path.
        Returns (onnx_path, json_path).
        """
        voice_path = Path(voice_name)
        if voice_path.is_file() and voice_path.suffix == ".onnx":
            json_path = voice_path.with_suffix(".onnx.json")
            if json_path.exists():
                return (voice_path.resolve(), json_path.resolve())

        # Search candidates in voices_dir or runtime/piper
        search_dirs = [
            self.voices_dir,
            RUNTIME_DIR / "piper",
            MODELS_DIR / "piper",
        ]
        
        # Clean extension if provided
        clean_name = voice_name[:-5] if voice_name.endswith(".onnx") else voice_name

        for s_dir in search_dirs:
            if not s_dir.exists():
                continue
            onnx_candidate = s_dir / f"{clean_name}.onnx"
            json_candidate = s_dir / f"{clean_name}.onnx.json"
            if onnx_candidate.exists() and json_candidate.exists():
                return (onnx_candidate.resolve(), json_candidate.resolve())

        return (None, None)

    def check_availability(self, voice_name: str) -> Tuple[bool, str, int]:
        """
        Validate executable and voice model availability.
        Returns (available, error_message, sample_rate).
        """
        exe = self.find_executable()
        if not exe or not exe.exists():
            return False, "Piper TTS executable not found in runtime/piper/ or system PATH.", 22050

        onnx_p, json_p = self.find_voice(voice_name)
        if not onnx_p or not json_p:
            return False, f"Piper voice model '{voice_name}' (.onnx and .onnx.json) not found in {self.voices_dir}.", 22050

        # Read sample rate from json config
        sample_rate = 22050
        try:
            with open(json_p, "r", encoding="utf-8") as f:
                v_config = json.load(f)
                sample_rate = v_config.get("audio", {}).get("sample_rate", 22050)
        except Exception as e:
            logger.warning(f"Could not parse sample rate from {json_p}: {e}")

        return True, "", sample_rate

    def synthesize(
        self,
        text: str,
        output_wav_path: Path,
        voice_name: str,
        timeout: int = 120,
        speaker: Optional[str] = None
    ) -> float:
        """
        Synthesize text into WAV file using Piper CLI process.
        Returns synthesis duration in seconds.
        """
        exe = self.find_executable()
        if not exe:
            raise PiperUnavailableError("Piper binary not found.")

        onnx_p, _ = self.find_voice(voice_name)
        if not onnx_p:
            raise PiperVoiceNotFoundError(f"Voice model '{voice_name}' not found.")

        output_wav_path.parent.mkdir(parents=True, exist_ok=True)

        cmd = [
            str(exe),
            "--model", str(onnx_p),
            "--output_file", str(output_wav_path)
        ]
        if speaker is not None:
            cmd.extend(["--speaker", str(speaker)])

        start_time = time.time()
        proc = None
        try:
            proc = subprocess.Popen(
                cmd,
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE
            )
            stdout_data, stderr_data = proc.communicate(
                input=text.strip().encode("utf-8"),
                timeout=timeout
            )
            elapsed = time.time() - start_time

            if proc.returncode != 0:
                err_text = stderr_data.decode("utf-8", errors="replace")
                raise PiperSynthesisError(f"Piper exited with code {proc.returncode}: {err_text}")

            return elapsed

        except subprocess.TimeoutExpired:
            if proc:
                proc.kill()
                proc.communicate()
            if output_wav_path.exists():
                try:
                    output_wav_path.unlink()
                except OSError:
                    pass
            raise PiperTimeoutError(f"Piper synthesis process timed out after {timeout} seconds.")
        except Exception as e:
            if not isinstance(e, AutoDubError):
                raise PiperSynthesisError(f"Subprocess invocation failed: {e}") from e
            raise


def validate_wav_file(file_path: Path) -> Dict[str, Any]:
    """Validate WAV audio file existence, header integrity, sample rate, channels, duration."""
    if not file_path.exists() or file_path.stat().st_size == 0:
        raise PiperInvalidOutputError(f"WAV audio file {file_path} is empty or missing.")

    try:
        with wave.open(str(file_path), "rb") as wf:
            channels = wf.getnchannels()
            sample_rate = wf.getframerate()
            nframes = wf.getnframes()
            duration = nframes / float(sample_rate) if sample_rate > 0 else 0.0

            if duration <= 0 or not math.isfinite(duration):
                raise PiperInvalidOutputError(f"Invalid audio duration ({duration}s) in {file_path}.")

            return {
                "channels": channels,
                "sample_rate": sample_rate,
                "duration": round(duration, 4),
                "format": "wav"
            }
    except wave.Error as e:
        raise PiperInvalidOutputError(f"Invalid or corrupted WAV file header in {file_path}: {e}") from e


class RealTTS:
    """Real Text-to-Speech stage runner using local Piper TTS engine."""

    def __init__(self, step_delay: float = 0.05, client: Optional[PiperClient] = None):
        self.step_delay = step_delay
        self.client = client or PiperClient()

    def run(
        self,
        project: Project,
        is_cancelled: Optional[Callable[[], bool]] = None,
        fail_at_step: Optional[int] = None,
        force: bool = False,
        voice_name: Optional[str] = None,
        language: str = "vi"
    ) -> float:
        stage_name = PipelineStage.TTS.value
        stage_info = project.get_stage_info(stage_name)
        start_time = time.time()

        audio_tts_dir = project.project_dir / "audio" / "tts"
        audio_tts_dir.mkdir(parents=True, exist_ok=True)
        partial_json_path = audio_tts_dir / "tts.partial.json"

        # Determine voice model name
        target_voice = (
            voice_name
            or project.data.get("tts", {}).get("voice")
            or project.data.get("config", {}).get("tts", {}).get("voice")
            or "vi_VN-viss-low"
        )

        completed_segment_ids = set()
        segment_metadata_map: Dict[str, Dict[str, Any]] = {}

        # Handle simulated step failure for pipeline state machine unit tests
        if fail_at_step is not None:
            err_msg = f"Simulated error in stage {stage_name} at step {fail_at_step}"
            failed_current = max(0, fail_at_step - 1)
            project.update_stage(stage_name, StageStatus.FAILED.value, current=failed_current, total=10, error=err_msg)
            emit_event("stage_error", stage_name, current=failed_current, total=10, error=err_msg)
            raise RuntimeError(err_msg)

        # 1. Idempotency Check
        if not force and stage_info.get("status") == StageStatus.COMPLETED.value:
            # Check if all TTS output files exist
            segments = project.data.get("segments", [])
            all_valid = len(segments) > 0
            for seg in segments:
                if seg.get("tts", {}).get("status") == "SKIPPED":
                    continue
                wav_file = audio_tts_dir / f"{seg.get('id', 1):06d}.wav"
                if not wav_file.exists() or wav_file.stat().st_size == 0:
                    all_valid = False
                    break
            if all_valid:
                logger.info("Existing valid TTS audio files found. Skipping TTS stage.")
                emit_event("progress", stage_name, current=100, total=100, percent=100.0, message="Existing valid TTS output found.")
                emit_event("stage_complete", stage_name, current=100, total=100, percent=100.0)
                return 0.0

        # 2. Piper & Voice Model Discovery Check
        available, err_msg, voice_sample_rate = self.client.check_availability(target_voice)
        if not available:
            logger.error(f"TTS Stage Error: {err_msg}")
            project.update_stage(stage_name, StageStatus.FAILED.value, error=err_msg)
            emit_event("stage_error", stage_name, error=err_msg)
            if "executable not found" in err_msg.lower():
                raise PiperUnavailableError(err_msg)
            else:
                raise PiperVoiceNotFoundError(err_msg)

        # 3. Load Translated Segments
        segments = project.data.get("segments", [])
        if not segments:
            translated_srt = project.project_dir / "transcript" / "translated.srt"
            if translated_srt.exists():
                segments = self._parse_srt(translated_srt)

        total_segments = len(segments)
        if total_segments == 0:
            logger.warning("No segments found for TTS synthesis.")
            project.update_stage(stage_name, StageStatus.COMPLETED.value, progress=100, current=0, total=0)
            emit_event("stage_complete", stage_name, current=0, total=0, percent=100.0)
            return 0.0

        # 4. Read Partial Checkpoint if resuming
        if not force and partial_json_path.exists():
            try:
                with open(partial_json_path, "r", encoding="utf-8") as f:
                    checkpoint_data = json.load(f)
                    completed_segment_ids = set(checkpoint_data.get("completed_segments", []))
                    segment_metadata_map = checkpoint_data.get("segments", {})
                    logger.info(f"Loaded TTS checkpoint: {len(completed_segment_ids)} completed segments.")
            except Exception as e:
                logger.warning(f"Could not load TTS partial checkpoint: {e}. Starting fresh.")

        # Update Project Stage State to RUNNING
        project.update_stage(stage_name, StageStatus.RUNNING.value, progress=0, current=0, total=total_segments)
        emit_event("stage_start", stage_name, current=0, total=total_segments, percent=0.0)

        total_audio_duration = 0.0

        for idx, seg in enumerate(segments):
            if is_cancelled and is_cancelled():
                err = "TTS stage cancelled by user."
                logger.warning(err)
                project.update_stage(stage_name, StageStatus.CANCELLED.value, current=idx, total=total_segments, error=err)
                emit_event("stage_cancelled", stage_name, current=idx, total=total_segments, error=err)
                self._save_partial_checkpoint(partial_json_path, target_voice, language, list(completed_segment_ids), segment_metadata_map)
                raise PipelineCancelledError(err)

            seg_id = seg.get("id", idx + 1)
            wav_filename = f"{seg_id:06d}.wav"
            final_wav_path = audio_tts_dir / wav_filename
            tmp_wav_path = audio_tts_dir / f"{wav_filename}.tmp"

            # Segment text selection: prefer translation, fallback to text
            tts_text = (seg.get("translation") or seg.get("text") or "").strip()

            # Handle Empty / Whitespace Segments
            if not tts_text:
                logger.info(f"Segment {seg_id} text is empty/whitespace. Skipping TTS synthesis.")
                seg_meta = {
                    "audio_file": f"audio/tts/{wav_filename}",
                    "status": "SKIPPED",
                    "reason": "EMPTY_TEXT",
                    "duration": 0.0
                }
                seg["tts"] = seg_meta
                completed_segment_ids.add(seg_id)
                segment_metadata_map[str(seg_id)] = seg_meta
                self._save_partial_checkpoint(partial_json_path, target_voice, language, list(completed_segment_ids), segment_metadata_map)
                continue

            # Check if segment already completed and valid
            if not force and seg_id in completed_segment_ids and final_wav_path.exists():
                try:
                    wav_info = validate_wav_file(final_wav_path)
                    seg["tts"] = {
                        "audio_file": f"audio/tts/{wav_filename}",
                        "duration": wav_info["duration"],
                        "sample_rate": wav_info["sample_rate"],
                        "channels": wav_info["channels"],
                        "format": "wav"
                    }
                    total_audio_duration += wav_info["duration"]
                    continue
                except PiperInvalidOutputError:
                    logger.warning(f"Segment {seg_id} audio corrupt. Re-synthesizing.")
                    completed_segment_ids.discard(seg_id)

            # Retry loop for synthesis (max 3 attempts with backoff)
            retries = 3
            backoff_delays = [1.0, 2.0, 4.0]
            synthesis_success = False
            last_err = None

            for attempt in range(retries):
                if is_cancelled and is_cancelled():
                    if tmp_wav_path.exists():
                        try: tmp_wav_path.unlink()
                        except OSError: pass
                    err = "TTS stage cancelled by user."
                    project.update_stage(stage_name, StageStatus.CANCELLED.value, current=idx, total=total_segments, error=err)
                    emit_event("stage_cancelled", stage_name, current=idx, total=total_segments, error=err)
                    self._save_partial_checkpoint(partial_json_path, target_voice, language, list(completed_segment_ids), segment_metadata_map)
                    raise PipelineCancelledError(err)

                try:
                    if tmp_wav_path.exists():
                        try: tmp_wav_path.unlink()
                        except OSError: pass

                    self.client.synthesize(
                        text=tts_text,
                        output_wav_path=tmp_wav_path,
                        voice_name=target_voice,
                        timeout=120,
                        speaker=seg.get("speaker")
                    )

                    # Validate generated temp WAV
                    wav_info = validate_wav_file(tmp_wav_path)

                    # Atomic Rename
                    if final_wav_path.exists():
                        final_wav_path.unlink()
                    tmp_wav_path.rename(final_wav_path)

                    seg_meta = {
                        "audio_file": f"audio/tts/{wav_filename}",
                        "duration": wav_info["duration"],
                        "sample_rate": wav_info["sample_rate"],
                        "channels": wav_info["channels"],
                        "format": "wav"
                    }
                    seg["tts"] = seg_meta
                    total_audio_duration += wav_info["duration"]

                    completed_segment_ids.add(seg_id)
                    segment_metadata_map[str(seg_id)] = seg_meta
                    self._save_partial_checkpoint(partial_json_path, target_voice, language, list(completed_segment_ids), segment_metadata_map)

                    synthesis_success = True
                    break

                except (PiperSynthesisError, PiperInvalidOutputError, PiperTimeoutError) as e:
                    last_err = e
                    logger.warning(f"Synthesis failed for segment {seg_id} (attempt {attempt + 1}/{retries}): {e}")
                    if tmp_wav_path.exists():
                        try: tmp_wav_path.unlink()
                        except OSError: pass
                    if attempt < retries - 1:
                        time.sleep(backoff_delays[attempt])

            if not synthesis_success:
                err_msg = f"TTS Synthesis failed for segment {seg_id} after {retries} retries: {last_err}"
                logger.error(err_msg)
                project.update_stage(stage_name, StageStatus.FAILED.value, current=idx, total=total_segments, error=err_msg)
                emit_event("stage_error", stage_name, current=idx, total=total_segments, error=err_msg)
                self._save_partial_checkpoint(partial_json_path, target_voice, language, list(completed_segment_ids), segment_metadata_map)
                raise TTSSynthesisFailedError(err_msg) from last_err

            # Emit progress for segment
            pct = round(((idx + 1) / total_segments) * 100, 2)
            elapsed_seg = round(time.time() - start_time, 2)
            project.update_stage(stage_name, StageStatus.RUNNING.value, progress=pct, current=idx + 1, total=total_segments)
            emit_event(
                "progress",
                stage_name,
                current=idx + 1,
                total=total_segments,
                percent=pct,
                segment_id=seg_id,
                elapsed=elapsed_seg
            )

        # 5. Create Optional Combined WAV File
        self._create_combined_audio(audio_tts_dir, segments)

        # 6. Update Project Data & Complete Stage
        total_time = time.time() - start_time
        rtf = total_time / total_audio_duration if total_audio_duration > 0 else 0.0

        project.data["tts"] = {
            "engine": "piper",
            "voice": target_voice,
            "language": language,
            "completed_segments": len(completed_segment_ids),
            "total_audio_duration": round(total_audio_duration, 4),
            "processing_time": round(total_time, 4),
            "rtf": round(rtf, 4)
        }
        project.data["segments"] = segments

        # Atomic Save Project Model
        project.update_stage(stage_name, StageStatus.COMPLETED.value, progress=100, current=total_segments, total=total_segments)
        project.save()

        # Clean up partial checkpoint upon full completion
        if partial_json_path.exists():
            try: partial_json_path.unlink()
            except OSError: pass

        emit_event("stage_complete", stage_name, current=total_segments, total=total_segments, percent=100.0)
        logger.info(f"TTS Stage completed successfully in {total_time:.2f}s (RTF: {rtf:.4f}).")

        return total_time

    def _save_partial_checkpoint(
        self,
        checkpoint_path: Path,
        voice: str,
        language: str,
        completed_ids: List[int],
        segment_meta: Dict[str, Any]
    ):
        """Atomically write tts.partial.json checkpoint file."""
        tmp_checkpoint = checkpoint_path.with_suffix(".tmp")
        data = {
            "engine": "piper",
            "voice": voice,
            "language": language,
            "completed_segments": sorted(list(completed_ids)),
            "segments": segment_meta
        }
        try:
            with open(tmp_checkpoint, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            tmp_checkpoint.replace(checkpoint_path)
        except Exception as e:
            logger.warning(f"Could not save TTS partial checkpoint: {e}")

    def _create_combined_audio(self, tts_dir: Path, segments: List[Dict[str, Any]]):
        """Concatenate individual segment WAVs into audio/tts/combined.wav."""
        combined_path = tts_dir / "combined.wav"
        wav_files = []
        for seg in segments:
            if seg.get("tts", {}).get("status") == "SKIPPED":
                continue
            seg_id = seg.get("id", 1)
            f_path = tts_dir / f"{seg_id:06d}.wav"
            if f_path.exists() and f_path.stat().st_size > 0:
                wav_files.append(f_path)

        if not wav_files:
            return

        try:
            params = None
            audio_frames = []
            for w_file in wav_files:
                with wave.open(str(w_file), "rb") as wf:
                    if params is None:
                        params = wf.getparams()
                    audio_frames.append(wf.readframes(wf.getnframes()))

            if params and audio_frames:
                with wave.open(str(combined_path), "wb") as wf:
                    wf.setparams(params)
                    for frame_data in audio_frames:
                        wf.writeframes(frame_data)
                logger.info(f"Combined WAV generated at {combined_path}")
        except Exception as e:
            logger.warning(f"Failed to generate combined.wav: {e}")

    def _parse_srt(self, srt_path: Path) -> List[Dict[str, Any]]:
        """Fallback SRT parser when segments array is missing in project.json."""
        segments = []
        with open(srt_path, "r", encoding="utf-8") as f:
            content = f.read().strip()

        blocks = content.split("\n\n")
        for block in blocks:
            lines = [l.strip() for l in block.split("\n") if l.strip()]
            if len(lines) >= 2:
                try:
                    seg_id = int(lines[0])
                    times = lines[1].split(" --> ")
                    start_sec = self._srt_time_to_seconds(times[0])
                    end_sec = self._srt_time_to_seconds(times[1])
                    text = " ".join(lines[2:]) if len(lines) >= 3 else ""
                    segments.append({
                        "id": seg_id,
                        "start": start_sec,
                        "end": end_sec,
                        "translation": text,
                        "text": text
                    })
                except Exception:
                    continue
        return segments

    @staticmethod
    def _srt_time_to_seconds(time_str: str) -> float:
        parts = time_str.replace(",", ".").split(":")
        hours = float(parts[0])
        minutes = float(parts[1])
        seconds = float(parts[2])
        return hours * 3600 + minutes * 60 + seconds


# Alias for backward compatibility / pipeline manager integration
PiperTTS = RealTTS
