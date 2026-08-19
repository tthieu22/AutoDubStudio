import signal
import sys
from pathlib import Path
from typing import Optional, Dict, Type, Any

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
from autodub.modules.renderer import RealRenderer
from autodub.pipeline.mocks import (
    MockTTS, MockSynchronizer, MockRenderer, MockBaseStage
)
from autodub.utils.files import ensure_project_structure
from autodub.utils.logging import setup_logger
from autodub.exceptions import (
    AutoDubError, StageDependencyError, StateTransitionError, PipelineCancelledError
)

STAGE_RUNNERS: Dict[PipelineStage, Any] = {
    PipelineStage.EXTRACT: RealExtractor,
    PipelineStage.TRANSCRIBE: RealTranscriber,
    PipelineStage.TRANSLATE: RealTranslator,
    PipelineStage.TTS: RealTTS,
    PipelineStage.SYNC: RealSynchronizer,
    PipelineStage.RENDER: RealRenderer,
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
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)

    def _signal_handler(self, signum, frame):
        self.logger.info(f"Received cancellation signal ({signum}). Requesting pipeline cancellation.")
        self._cancel_requested = True

    def cancel(self):
        self._cancel_requested = True

    def is_cancelled(self) -> bool:
        return self._cancel_requested

    def validate(self) -> bool:
        return ProjectValidator.validate(self.project)

    def run_stage(self, stage_enum: PipelineStage, force: bool = False, fail_at_step: Optional[int] = None):
        self.validate()
        stage_name = stage_enum.value
        stage_info = self.project.get_stage_info(stage_name)
        current_status = StageStatus(stage_info["status"])

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
        runner_cls = STAGE_RUNNERS[stage_enum]
        runner = runner_cls(step_delay=self.step_delay)

        try:
            runner.run(self.project, is_cancelled=self.is_cancelled, fail_at_step=fail_at_step)
            self.logger.info(f"Completed stage {stage_name.upper()}")
        except PipelineCancelledError as e:
            self.logger.warning(f"Cancelled stage {stage_name.upper()}: {e}")
            raise
        except Exception as e:
            self.logger.error(f"Failed stage {stage_name.upper()}: {e}")
            raise

    def run_all(self, fail_at_stage: Optional[PipelineStage] = None, fail_at_step: Optional[int] = None):
        for stage in STAGE_ORDER:
            stage_info = self.project.get_stage_info(stage.value)
            if stage_info["status"] == StageStatus.COMPLETED.value:
                self.logger.info(f"Skipping completed stage {stage.value.upper()}")
                continue
            
            target_fail_step = fail_at_step if (fail_at_stage and stage == fail_at_stage) else None
            self.run_stage(stage, fail_at_step=target_fail_step)

    def resume(self):
        """Find first non-COMPLETED stage and continue execution from checkpoint."""
        self.validate()
        self.logger.info(f"Resuming pipeline for project '{self.project.data.get('name')}'")
        self.run_all()

    def retry(self, stage_enum: PipelineStage, force: bool = False):
        """Retry a failed or cancelled stage (or completed stage if force=True)."""
        stage_info = self.project.get_stage_info(stage_enum.value)
        status = StageStatus(stage_info["status"])

        if status == StageStatus.COMPLETED and not force:
            raise StateTransitionError(f"Stage '{stage_enum.value}' is already COMPLETED. Use --force to retry.")

        if status in (StageStatus.FAILED, StageStatus.CANCELLED, StageStatus.PENDING) or force:
            self.run_stage(stage_enum, force=force)
            # After retrying this stage, continue subsequent stages
            stage_idx = STAGE_ORDER.index(stage_enum)
            for next_stage in STAGE_ORDER[stage_idx + 1:]:
                next_info = self.project.get_stage_info(next_stage.value)
                if next_info["status"] != StageStatus.COMPLETED.value:
                    self.run_stage(next_stage)

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
