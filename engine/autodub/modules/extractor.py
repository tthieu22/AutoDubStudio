import time
from pathlib import Path
from typing import Optional, Callable

from autodub.models.project import Project
from autodub.pipeline.state import PipelineStage, StageStatus
from autodub.pipeline.progress import emit_event
from autodub.utils.ffmpeg import FFmpegRunner
from autodub.exceptions import AutoDubError, PipelineCancelledError

class RealExtractor:
    def __init__(self, step_delay: float = 0.0, ffmpeg_runner: Optional[FFmpegRunner] = None):
        self.runner = ffmpeg_runner or FFmpegRunner()

    def run(
        self,
        project: Project,
        is_cancelled: Optional[Callable[[], bool]] = None,
        force: bool = False,
        fail_at_step: Optional[int] = None
    ):
        stage_name = PipelineStage.EXTRACT.value
        project_dir = project.project_dir
        rel_source = project.data.get("source", {}).get("path", "source/input.mp4")
        input_video = (project_dir / rel_source).resolve()

        if not input_video.exists():
            raise AutoDubError(f"Input video file not found: {input_video}")

        output_audio = project_dir / "audio" / "original.wav"
        output_tmp = output_audio.with_suffix(".wav.tmp")

        # 1. Idempotency Check
        if output_audio.exists() and not force:
            try:
                valid_audio_meta = self.runner.validate_wav(output_audio)
                emit_event("progress", stage_name, current=100, total=100, percent=100.0, message="Existing valid audio found.")
                project.update_stage(stage_name, StageStatus.COMPLETED.value, progress=100, current=100, total=100)
                emit_event("stage_complete", stage_name, current=100, total=100)
                return
            except AutoDubError:
                # Corrupt output file, remove and re-extract
                output_audio.unlink(missing_ok=True)

        # 2. Probe Media Metadata
        media_meta = self.runner.probe(input_video)
        if not media_meta.get("has_audio"):
            raise AutoDubError("No audio stream found in input video.")

        if "metadata" not in project.data:
            project.data["metadata"] = {}
        project.data["metadata"]["media"] = media_meta
        project.save()

        total_duration = media_meta.get("duration", 0.0)
        project.update_stage(stage_name, StageStatus.RUNNING.value, progress=0, current=0, total=int(total_duration))
        emit_event("stage_start", stage_name, current=0, total=int(total_duration))

        def progress_cb(current_sec: float, total_sec: float):
            pct = min(100.0, (current_sec / total_sec) * 100.0) if total_sec > 0 else 0.0
            project.update_stage(stage_name, StageStatus.RUNNING.value, progress=int(pct), current=int(current_sec), total=int(total_sec))
            emit_event("progress", stage_name, current=int(current_sec), total=int(total_sec), percent=pct)

        # 3. Extraction to atomic .tmp file
        try:
            processing_time = self.runner.run_extraction(
                input_video,
                output_tmp,
                total_duration=total_duration,
                progress_callback=progress_cb,
                is_cancelled=is_cancelled
            )

            # 4. Output Validation
            wav_meta = self.runner.validate_wav(output_tmp)

            # Atomic replace tmp -> original.wav
            if output_tmp.exists():
                output_tmp.replace(output_audio)

            # 5. Save Project Metadata
            project.data["metadata"]["audio"] = {
                "path": "audio/original.wav",
                "duration": wav_meta.get("duration", total_duration),
                "sample_rate": wav_meta.get("audio_sample_rate", 16000),
                "channels": wav_meta.get("audio_channels", 1),
                "codec": wav_meta.get("audio_codec", "pcm_s16le")
            }
            if "processing" not in project.data["metadata"]:
                project.data["metadata"]["processing"] = {}
            project.data["metadata"]["processing"]["extract_seconds"] = processing_time
            project.save()

            project.update_stage(stage_name, StageStatus.COMPLETED.value, progress=100, current=int(total_duration), total=int(total_duration))
            emit_event("stage_complete", stage_name, current=int(total_duration), total=int(total_duration))

        except PipelineCancelledError as e:
            if output_tmp.exists():
                output_tmp.unlink(missing_ok=True)
            project.update_stage(stage_name, StageStatus.CANCELLED.value, error=str(e))
            emit_event("stage_cancelled", stage_name, error=str(e))
            raise
        except Exception as e:
            if output_tmp.exists():
                output_tmp.unlink(missing_ok=True)
            project.update_stage(stage_name, StageStatus.FAILED.value, error=str(e))
            emit_event("stage_error", stage_name, error=str(e))
            raise
