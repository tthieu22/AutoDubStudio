import gc
import json
import logging
import os
import shutil
import subprocess
import time
from pathlib import Path
from typing import Dict, Any, List, Optional, Callable

from autodub.config import MODELS_DIR
from autodub.models.project import Project
from autodub.pipeline.state import PipelineStage, StageStatus
from autodub.pipeline.progress import emit_event
from autodub.utils.ffmpeg import FFmpegRunner, find_ffmpeg
from autodub.exceptions import AutoDubError, PipelineCancelledError

logger = logging.getLogger("autodub")

def format_srt_timestamp(seconds: float) -> str:
    """Format seconds float into SRT timestamp format HH:MM:SS,mmm."""
    if seconds < 0:
        seconds = 0.0
    millis = int(round((seconds - int(seconds)) * 1000))
    if millis >= 1000:
        seconds += 1.0
        millis = 0
    total_sec = int(seconds)
    hours = total_sec // 3600
    minutes = (total_sec % 3600) // 60
    secs = total_sec % 60
    return f"{hours:02d}:{minutes:02d}:{secs:02d},{millis:03d}"

def validate_srt_content(srt_text: str) -> bool:
    """Validate SRT text format and continuous segment numbering."""
    content = srt_text.strip()
    if not content:
        return True  # Valid empty SRT for audio with no spoken text
    blocks = content.split("\n\n")
    for block in blocks:
        lines = block.strip().split("\n")
        if len(lines) < 2:
            return False
        if not lines[0].isdigit():
            return False
        if "-->" not in lines[1]:
            return False
    return True

class RealTranscriber:
    def __init__(
        self,
        step_delay: float = 0.0,
        model_name: str = "small",
        device: str = "auto",
        compute_type: str = "int8",
        chunk_duration: int = 600
    ):
        self.step_delay = step_delay
        self.model_name = model_name
        self.device_setting = device
        self.compute_type = compute_type
        self.chunk_duration = chunk_duration
        self.whisper_model = None
        self.active_device = None

    def _init_whisper_model(self):
        """Initialize faster-whisper model with device selection and CPU fallback."""
        if self.whisper_model is not None:
            return

        from faster_whisper import WhisperModel

        whisper_dir = MODELS_DIR / "whisper"
        whisper_dir.mkdir(parents=True, exist_ok=True)

        target_device = self.device_setting.lower()

        if target_device == "auto":
            try:
                logger.info(f"Attempting faster-whisper CUDA initialization (model={self.model_name}, compute_type={self.compute_type})...")
                self.whisper_model = WhisperModel(
                    self.model_name,
                    device="cuda",
                    compute_type=self.compute_type,
                    download_root=str(whisper_dir)
                )
                self.active_device = "cuda"
                logger.info("faster-whisper CUDA initialized successfully.")
            except Exception as e:
                logger.warning(f"CUDA unavailable or failed to initialize ({e}). Falling back to CPU.")
                self.whisper_model = WhisperModel(
                    self.model_name,
                    device="cpu",
                    compute_type="int8",
                    download_root=str(whisper_dir)
                )
                self.active_device = "cpu"
                logger.info("faster-whisper CPU initialized successfully.")
        elif target_device == "cuda":
            try:
                self.whisper_model = WhisperModel(
                    self.model_name,
                    device="cuda",
                    compute_type=self.compute_type,
                    download_root=str(whisper_dir)
                )
                self.active_device = "cuda"
            except Exception as e:
                raise AutoDubError(f"CUDA device explicitly requested but failed to initialize: {e}")
        else:
            self.whisper_model = WhisperModel(
                self.model_name,
                device="cpu",
                compute_type="int8",
                download_root=str(whisper_dir)
            )
            self.active_device = "cpu"

    def _create_audio_chunks(self, audio_path: Path, output_chunks_dir: Path, total_duration: float) -> List[Dict[str, Any]]:
        """Split audio file into 10-minute (600s) chunk files using FFmpeg."""
        output_chunks_dir.mkdir(parents=True, exist_ok=True)
        ffmpeg_bin = str(find_ffmpeg())
        chunks_info = []

        chunk_sec = self.chunk_duration
        num_chunks = max(1, int((total_duration + chunk_sec - 1) // chunk_sec))

        for idx in range(num_chunks):
            start_time = idx * chunk_sec
            duration = min(chunk_sec, total_duration - start_time)
            chunk_file = output_chunks_dir / f"chunk_{idx:04d}.wav"

            if not chunk_file.exists() or chunk_file.stat().st_size == 0:
                cmd = [
                    ffmpeg_bin, "-y",
                    "-ss", str(start_time),
                    "-t", str(duration),
                    "-i", str(audio_path),
                    "-c", "copy",
                    str(chunk_file)
                ]
                subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)

            chunks_info.append({
                "index": idx,
                "file": chunk_file,
                "start_time": start_time,
                "duration": duration
            })

        return chunks_info

    def run(
        self,
        project: Project,
        is_cancelled: Optional[Callable[[], bool]] = None,
        force: bool = False,
        fail_at_step: Optional[int] = None
    ):
        stage_name = PipelineStage.TRANSCRIBE.value
        project_dir = project.project_dir
        audio_path = project_dir / "audio" / "original.wav"
        output_srt = project_dir / "transcript" / "original.srt"
        output_tmp = output_srt.with_suffix(".srt.tmp")
        partial_json_file = project_dir / "transcript" / "original.partial.json"

        # 1. Idempotency Check
        if output_srt.exists() and not force:
            try:
                with open(output_srt, "r", encoding="utf-8") as f:
                    content = f.read()
                if validate_srt_content(content):
                    emit_event("progress", stage_name, current=100, total=100, percent=100.0, message="Existing valid SRT transcript found.")
                    project.update_stage(stage_name, StageStatus.COMPLETED.value, progress=100, current=100, total=100)
                    emit_event("stage_complete", stage_name, current=100, total=100)
                    return
            except Exception:
                output_srt.unlink(missing_ok=True)

        # 2. Audio File Validation
        ffmpeg_runner = FFmpegRunner()
        audio_meta = ffmpeg_runner.validate_wav(audio_path)
        total_duration = audio_meta["duration"]

        if total_duration <= 0:
            raise AutoDubError("Audio file has 0 duration.")

        # 3. Load Partial Checkpoint if exists
        completed_chunks = set()
        all_segments: List[Dict[str, Any]] = []
        detected_language = project.data.get("source", {}).get("language", "en")
        language_prob = 1.0

        if partial_json_file.exists() and not force:
            try:
                with open(partial_json_file, "r", encoding="utf-8") as f:
                    part_data = json.load(f)
                completed_chunks = set(part_data.get("completed_chunks", []))
                all_segments = part_data.get("segments", [])
                detected_language = part_data.get("language", detected_language)
                language_prob = part_data.get("language_probability", 1.0)
            except Exception:
                completed_chunks = set()
                all_segments = []

        # 4. Create Audio Chunks
        chunks_dir = project_dir / "audio" / "chunks"
        chunks = self._create_audio_chunks(audio_path, chunks_dir, total_duration)
        total_chunks = len(chunks)

        # 5. Initialize Model
        proj_settings = project.data.get("settings", {})
        self.model_name = proj_settings.get("whisper_model", self.model_name)
        self.device_setting = proj_settings.get("whisper_device", proj_settings.get("device", "auto"))
        self.compute_type = proj_settings.get("whisper_compute_type", self.compute_type)

        self._init_whisper_model()

        project.update_stage(stage_name, StageStatus.RUNNING.value, progress=0, current=len(completed_chunks), total=total_chunks)
        emit_event("stage_start", stage_name, current=len(completed_chunks), total=total_chunks)

        source_lang = project.data.get("source", {}).get("language", "en")
        lang_param = None if source_lang == "auto" else source_lang

        start_job_time = time.time()

        try:
            for chunk_info in chunks:
                idx = chunk_info["index"]
                if is_cancelled and is_cancelled():
                    project.update_stage(stage_name, StageStatus.CANCELLED.value, current=idx, total=total_chunks)
                    emit_event("stage_cancelled", stage_name, current=idx, total=total_chunks)
                    raise PipelineCancelledError("Transcription stage cancelled by user.")

                if fail_at_step is not None and (idx + 1) == fail_at_step:
                    err_msg = f"Simulated transcription failure at chunk {idx + 1}"
                    project.update_stage(stage_name, StageStatus.FAILED.value, error=err_msg)
                    emit_event("stage_error", stage_name, error=err_msg)
                    raise RuntimeError(err_msg)

                if idx in completed_chunks:
                    continue

                emit_event("chunk_start", stage_name, chunk=idx + 1, total_chunks=total_chunks)

                # Transcribe chunk audio
                segments_iter, info = self.whisper_model.transcribe(
                    str(chunk_info["file"]),
                    language=lang_param,
                    beam_size=5,
                    vad_filter=True
                )

                if info and hasattr(info, "language"):
                    detected_language = info.language
                    language_prob = round(getattr(info, "language_probability", 1.0), 2)

                offset = chunk_info["start_time"]
                for seg in segments_iter:
                    text_clean = seg.text.strip()
                    if not text_clean:
                        continue
                    
                    seg_start = round(seg.start + offset, 3)
                    seg_end = round(seg.end + offset, 3)
                    
                    if seg_end <= seg_start:
                        seg_end = seg_start + 0.5

                    all_segments.append({
                        "id": len(all_segments) + 1,
                        "start": seg_start,
                        "end": seg_end,
                        "text": text_clean
                    })

                completed_chunks.add(idx)

                # Save partial checkpoint
                partial_json_file.parent.mkdir(parents=True, exist_ok=True)
                with open(partial_json_file, "w", encoding="utf-8") as f:
                    json.dump({
                        "completed_chunks": list(completed_chunks),
                        "segments": all_segments,
                        "language": detected_language,
                        "language_probability": language_prob
                    }, f, indent=2, ensure_ascii=False)

                pct = round((len(completed_chunks) / total_chunks) * 100, 2)
                project.update_stage(stage_name, StageStatus.RUNNING.value, progress=int(pct), current=len(completed_chunks), total=total_chunks)
                emit_event("progress", stage_name, current=len(completed_chunks), total=total_chunks, percent=pct)

            # Sort & sanitize global segments
            all_segments.sort(key=lambda s: s["start"])
            for i, seg in enumerate(all_segments):
                seg["id"] = i + 1

            # 6. Generate SRT Content
            srt_lines = []
            for seg in all_segments:
                srt_lines.append(str(seg["id"]))
                srt_lines.append(f"{format_srt_timestamp(seg['start'])} --> {format_srt_timestamp(seg['end'])}")
                srt_lines.append(seg["text"])
                srt_lines.append("")

            srt_content = "\n".join(srt_lines).strip() + "\n"

            if not validate_srt_content(srt_content):
                raise AutoDubError("Generated SRT content failed validation.")

            # Write atomic SRT
            output_tmp.parent.mkdir(parents=True, exist_ok=True)
            with open(output_tmp, "w", encoding="utf-8") as f:
                f.write(srt_content)

            if output_tmp.exists():
                output_tmp.replace(output_srt)

            # Save project data
            processing_time = round(time.time() - start_job_time, 2)
            project.data["segments"] = all_segments
            if "metadata" not in project.data:
                project.data["metadata"] = {}
            project.data["metadata"]["transcription"] = {
                "model": self.model_name,
                "device": self.active_device,
                "compute_type": self.compute_type,
                "language": detected_language,
                "language_probability": language_prob,
                "segments_count": len(all_segments)
            }
            if "processing" not in project.data["metadata"]:
                project.data["metadata"]["processing"] = {}
            project.data["metadata"]["processing"]["transcribe_seconds"] = processing_time
            project.save()

            # Cleanup temporary chunks and partial file
            if chunks_dir.exists():
                shutil.rmtree(chunks_dir, ignore_errors=True)
            if partial_json_file.exists():
                partial_json_file.unlink(missing_ok=True)

            project.update_stage(stage_name, StageStatus.COMPLETED.value, progress=100, current=total_chunks, total=total_chunks)
            emit_event("stage_complete", stage_name, current=total_chunks, total=total_chunks)

        except PipelineCancelledError as e:
            project.update_stage(stage_name, StageStatus.CANCELLED.value, error=str(e))
            emit_event("stage_cancelled", stage_name, error=str(e))
            raise
        except Exception as e:
            project.update_stage(stage_name, StageStatus.FAILED.value, error=str(e))
            emit_event("stage_error", stage_name, error=str(e))
            raise
        finally:
            # Memory Cleanup
            self.whisper_model = None
            gc.collect()
            try:
                import torch
                if torch.cuda.is_available():
                    torch.cuda.empty_cache()
            except ImportError:
                pass
