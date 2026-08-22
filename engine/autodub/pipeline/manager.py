import json
import logging
import os
import shutil
import signal
import sys
import time
from pathlib import Path
from typing import Optional, Dict, Type, Any, List

from autodub.config import PROJECTS_DIR
from autodub.models.project import Project
from autodub.pipeline.state import STAGE_ORDER, PipelineStage, StageStatus, validate_state_transition, get_previous_stage
from autodub.pipeline.validator import ProjectValidator
from autodub.pipeline.progress import emit_event
from autodub.modules.extractor import RealExtractor
from autodub.modules.transcriber import RealTranscriber
from autodub.modules.translator import RealTranslator
from autodub.modules.tts import RealTTS
from autodub.modules.synchronizer import RealSynchronizer
from autodub.modules.renderer import RealRenderer, validate_rendered_output
from autodub.utils.ffmpeg import FFmpegRunner
from autodub.utils.files import ensure_project_structure
from autodub.utils.logging import setup_logger
from autodub.exceptions import (
    AutoDubError, StageDependencyError, StateTransitionError, PipelineCancelledError, ArtifactValidationError
)

STAGE_RUNNERS: Dict[PipelineStage, Any] = {
    PipelineStage.EXTRACT: RealExtractor,
    PipelineStage.TRANSCRIBE: RealTranscriber,
    PipelineStage.TRANSLATE: RealTranslator,
    PipelineStage.TTS: RealTTS,
    PipelineStage.SYNC: RealSynchronizer,
    PipelineStage.RENDER: RealRenderer,
}

STAGE_WEIGHTS: Dict[PipelineStage, float] = {
    PipelineStage.EXTRACT: 10.0,
    PipelineStage.TRANSCRIBE: 25.0,
    PipelineStage.TRANSLATE: 15.0,
    PipelineStage.TTS: 20.0,
    PipelineStage.SYNC: 10.0,
    PipelineStage.RENDER: 20.0,
}


class PipelineManager:
    def __init__(self, project_identifier: str, step_delay: float = 0.05):
        project_path = Path(project_identifier)
        if project_path.is_absolute() or ("/" in project_identifier or "\\" in project_identifier):
            self.project_dir = project_path
        else:
            self.project_dir = PROJECTS_DIR / project_identifier

        self.step_delay = step_delay
        self.project_dir.mkdir(parents=True, exist_ok=True)
        ensure_project_structure(self.project_dir)

        self.logger = setup_logger(self.project_dir / "logs" / "pipeline.log")
        self.project = Project(self.project_dir)
        self._cancel_requested = False

        # Register signal handlers for SIGINT/SIGTERM cancellation
        try:
            signal.signal(signal.SIGINT, self._signal_handler)
            signal.signal(signal.SIGTERM, self._signal_handler)
        except (ValueError, TypeError):
            # Signal handling may fail if called outside main thread in tests
            pass

    def _signal_handler(self, signum, frame):
        self.logger.info(f"Received cancellation signal ({signum}). Requesting pipeline cancellation.")
        self._cancel_requested = True

    def cancel(self):
        self._cancel_requested = True

    def is_cancelled(self) -> bool:
        return self._cancel_requested

    def validate(self) -> bool:
        return ProjectValidator.validate(self.project)

    def preflight_check(self, strict: bool = False) -> None:
        """Perform preflight checks before running the pipeline."""
        self.validate()

        # 1. Verify FFmpeg & FFprobe
        runner = FFmpegRunner()
        if not runner.ffmpeg_path.exists() and not shutil.which("ffmpeg"):
            raise AutoDubError(f"FFmpeg binary not found at '{runner.ffmpeg_path}' or system PATH. Please install FFmpeg.")
        if not runner.ffprobe_path.exists() and not shutil.which("ffprobe"):
            raise AutoDubError(f"FFprobe binary not found at '{runner.ffprobe_path}' or system PATH. Please install FFprobe.")

        # 2. Verify source input video
        rel_src = self.project.data.get("source", {}).get("path", "source/input.mp4")
        source_path = Path(rel_src) if Path(rel_src).is_absolute() else self.project_dir / rel_src
        if not source_path.exists() or source_path.stat().st_size == 0:
            raise AutoDubError(f"Source video file '{source_path}' does not exist or is 0 bytes. Please re-create the project with a valid video file.")

        # 3. Disk space check (estimate at least 3x source video size required)
        try:
            stat = shutil.disk_usage(str(self.project_dir))
            video_size = source_path.stat().st_size
            required_space = max(100 * 1024 * 1024, video_size * 3)
            if stat.free < required_space:
                free_mb = stat.free / (1024 * 1024)
                req_mb = required_space / (1024 * 1024)
                raise AutoDubError(f"Insufficient disk space in '{self.project_dir}'. Free: {free_mb:.1f}MB, Required: ~{req_mb:.1f}MB")
        except OSError:
            pass

    def calculate_overall_progress(self, current_stage: PipelineStage, stage_percent: float) -> float:
        total_completed = 0.0
        for stage in STAGE_ORDER:
            weight = STAGE_WEIGHTS[stage]
            status = self.project.get_stage_info(stage.value)["status"]
            if stage == current_stage:
                total_completed += (stage_percent / 100.0) * weight
            elif status == StageStatus.COMPLETED.value:
                total_completed += weight

        return min(100.0, round(total_completed, 2))

    def validate_stage_artifact(self, stage_enum: PipelineStage) -> bool:
        """Validate if expected artifact for a stage exists and is non-empty."""
        p_dir = self.project_dir
        if stage_enum == PipelineStage.EXTRACT:
            f = p_dir / "audio" / "original.wav"
            return f.exists() and f.stat().st_size > 0
        elif stage_enum == PipelineStage.TRANSCRIBE:
            f = p_dir / "transcript" / "original.srt"
            return f.exists() and f.stat().st_size > 0
        elif stage_enum == PipelineStage.TRANSLATE:
            f = p_dir / "transcript" / "translated.srt"
            return f.exists() and f.stat().st_size > 0
        elif stage_enum == PipelineStage.TTS:
            f = p_dir / "audio" / "synced" / "combined.wav"
            tts_dir = p_dir / "audio" / "tts"
            return (f.exists() and f.stat().st_size > 0) or (tts_dir.exists() and len(list(tts_dir.glob("*.wav"))) > 0)
        elif stage_enum == PipelineStage.SYNC:
            f = p_dir / "audio" / "synced" / "combined.wav"
            return f.exists() and f.stat().st_size > 0
        elif stage_enum == PipelineStage.RENDER:
            f = p_dir / "output" / "final.mp4"
            if not f.exists() or f.stat().st_size == 0:
                return False
            try:
                runner = FFmpegRunner()
                validate_rendered_output(f, runner=runner)
                return True
            except Exception:
                return False
        return False

    def run_stage(self, stage_enum: PipelineStage, force: bool = False, fail_at_step: Optional[int] = None, **kwargs):
        self.validate()
        stage_name = stage_enum.value
        stage_info = self.project.get_stage_info(stage_name)
        current_status = StageStatus(stage_info["status"])

        # Check idempotency / valid artifact skip
        if not force and current_status == StageStatus.COMPLETED and self.validate_stage_artifact(stage_enum):
            self.logger.info(f"Skipping completed valid stage {stage_name.upper()}")
            emit_event("stage_skipped", stage=stage_name, message=f"Existing valid artifact found for stage {stage_name.upper()}.")
            return

        # State transition validation
        validate_state_transition(current_status, StageStatus.RUNNING, force=force)

        # Dependency check
        prev_stage = get_previous_stage(stage_enum)
        if prev_stage:
            prev_info = self.project.get_stage_info(prev_stage.value)
            if prev_info["status"] != StageStatus.COMPLETED.value:
                raise StageDependencyError(
                    f"Cannot run stage '{stage_name}'. Required previous stage '{prev_stage.value}' is {prev_info['status']}."
                )

        self.logger.info(f"Starting stage {stage_name.upper()}")
        emit_event("stage_start", stage=stage_name)

        runner_cls = STAGE_RUNNERS[stage_enum]
        runner = runner_cls(step_delay=self.step_delay)

        start_t = time.time()
        try:
            runner.run(self.project, force=force, is_cancelled=self.is_cancelled, fail_at_step=fail_at_step, **kwargs)
            duration = time.time() - start_t

            # Record timing metadata
            metadata = self.project.data.setdefault("metadata", {})
            timing = metadata.setdefault("timing", {})
            timing[stage_name] = round(duration, 3)
            self.project.save()

            self.logger.info(f"Completed stage {stage_name.upper()} (duration={duration:.2f}s)")
            emit_event("stage_complete", stage=stage_name, elapsed=duration)

            # Perform stage post-validation
            if stage_enum == PipelineStage.RENDER:
                final_mp4 = self.project_dir / "output" / "final.mp4"
                runner_ff = FFmpegRunner()
                validate_rendered_output(final_mp4, runner=runner_ff)

        except PipelineCancelledError as e:
            self.logger.warning(f"Cancelled stage {stage_name.upper()}: {e}")
            emit_event("stage_cancelled", stage=stage_name, error=str(e))
            raise
        except Exception as e:
            self.logger.error(f"Failed stage {stage_name.upper()}: {e}")
            emit_event("stage_error", stage=stage_name, error=str(e))
            raise

    def reset_all_stages(self):
        """Reset all pipeline stages to PENDING status."""
        for stage in STAGE_ORDER:
            self.project.update_stage(
                stage.value,
                status=StageStatus.PENDING.value,
                progress=0,
                current=0,
                total=0,
                error=None
            )
        self.logger.info("All pipeline stages reset to PENDING.")

    def run_all(self, fail_at_stage: Optional[PipelineStage] = None, fail_at_step: Optional[int] = None, force: bool = False, stop_at: Optional[PipelineStage] = None):
        if force:
            self.reset_all_stages()
        self.preflight_check()
        emit_event("pipeline_start", stage="PIPELINE", project=self.project.data.get("name"))

        start_t = time.time()
        try:
            for stage in STAGE_ORDER:
                if stop_at and STAGE_ORDER.index(stage) > STAGE_ORDER.index(stop_at):
                    self.logger.info(f"Stopping pipeline at {stage.value} as stop_at={stop_at.value} is reached.")
                    break

                stage_info = self.project.get_stage_info(stage.value)

                if not force and stage_info["status"] == StageStatus.COMPLETED.value and self.validate_stage_artifact(stage):
                    self.logger.info(f"Skipping completed valid stage {stage.value.upper()}")
                    emit_event("stage_skipped", stage=stage.value, message=f"Stage {stage.value.upper()} already completed.")
                    continue

                target_fail_step = fail_at_step if (fail_at_stage and stage == fail_at_stage) else None
                self.run_stage(stage, force=force, fail_at_step=target_fail_step)

            total_duration = time.time() - start_t
            timing = self.project.data.setdefault("metadata", {}).setdefault("timing", {})
            timing["total"] = round(total_duration, 3)
            self.project.save()

            self.logger.info(f"Pipeline completed successfully in {total_duration:.2f}s")
            emit_event("pipeline_complete", stage="PIPELINE", elapsed=total_duration, output_path=str(self.project_dir / "output" / "final.mp4"))

        except PipelineCancelledError as e:
            self.logger.warning(f"Pipeline cancelled: {e}")
            emit_event("pipeline_cancelled", stage="PIPELINE", error=str(e))
            raise
        except Exception as e:
            self.logger.error(f"Pipeline failed: {e}")
            emit_event("pipeline_error", stage="PIPELINE", error=str(e))
            raise

    def resume(self, stop_at: Optional[PipelineStage] = None):
        """Find first non-COMPLETED stage and continue execution from checkpoint."""
        self.preflight_check()
        self.logger.info(f"Resuming pipeline for project '{self.project.data.get('name')}'")
        self.run_all(stop_at=stop_at)

    def retry(self, stage_enum: PipelineStage, force: bool = False):
        """Retry a failed or cancelled stage (or completed stage if force=True)."""
        stage_info = self.project.get_stage_info(stage_enum.value)
        raw_status = (stage_info.get("status") or "pending").lower()
        try:
            status = StageStatus(raw_status)
        except ValueError:
            status = StageStatus.PENDING

        if status == StageStatus.COMPLETED and not force:
            raise StateTransitionError(f"Stage '{stage_enum.value}' is already COMPLETED. Use --force to retry.")

        if status in (StageStatus.FAILED, StageStatus.CANCELLED, StageStatus.PENDING) or force:
            # Reset target stage and all subsequent stages to PENDING first
            stage_idx = STAGE_ORDER.index(stage_enum)
            for st in STAGE_ORDER[stage_idx:]:
                self.project.update_stage(
                    st.value,
                    status=StageStatus.PENDING.value,
                    progress=0,
                    current=0,
                    total=0,
                    error=None
                )
            self.logger.info(f"Reset stages from {stage_enum.value.upper()} onwards to PENDING.")

            self.run_stage(stage_enum, force=force)
            # After retrying this stage, continue subsequent stages
            for next_stage in STAGE_ORDER[stage_idx + 1:]:
                next_info = self.project.get_stage_info(next_stage.value)
                if next_info["status"] != StageStatus.COMPLETED.value or not self.validate_stage_artifact(next_stage):
                    self.run_stage(next_stage, force=True)


    def get_status_formatted(self) -> str:
        lines = [f"Project: {self.project.data.get('name')}", ""]
        current_stage = None

        for stage in STAGE_ORDER:
            info = self.project.get_stage_info(stage.value)
            status_str = info['status'].upper()
            progress = info.get('progress', 0)
            lines.append(f"{stage.value.upper():<12} {status_str:<12} {progress:>3}%")
            if info['status'] == StageStatus.RUNNING.value:
                current_stage = stage.value.upper()
            elif current_stage is None and info['status'] in (StageStatus.PENDING.value, StageStatus.FAILED.value, StageStatus.CANCELLED.value):
                current_stage = stage.value.upper()

        lines.append("")
        lines.append(f"Current stage: {current_stage or 'NONE (COMPLETED)'}")
        return "\n".join(lines)
