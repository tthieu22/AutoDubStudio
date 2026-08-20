import json
import logging
import time
from pathlib import Path
from typing import Dict, Any, List, Optional

from autodub.jobs.job import Job
from autodub.jobs.job_state import JobState
from autodub.orchestration.pipeline_context import PipelineContext
from autodub.orchestration.retry_policy import RetryPolicy
from autodub.orchestration.stage_executor import (
    BaseStageExecutor,
    IngestStageExecutor,
    TranscribeStageExecutor,
    TranslateStageExecutor,
    TTSStageExecutor,
    SubtitleStageExecutor,
    MixStageExecutor,
    RenderStageExecutor,
    ValidateStageExecutor,
)
from autodub.utils.files import atomic_write_json
from autodub.exceptions import PipelineCancelledError, StageExecutionError, ArtifactValidationError

logger = logging.getLogger("autodub.orchestration.orchestrator")

STAGE_WEIGHTS: Dict[str, float] = {
    "INGEST": 5.0,
    "TRANSCRIBE": 20.0,
    "TRANSLATE": 10.0,
    "TTS": 20.0,
    "SUBTITLE": 5.0,
    "MIX": 10.0,
    "RENDER": 25.0,
    "VALIDATE": 5.0,
}

STAGE_SEQUENCE: List[str] = [
    "INGEST",
    "TRANSCRIBE",
    "TRANSLATE",
    "TTS",
    "SUBTITLE",
    "MIX",
    "RENDER",
    "VALIDATE",
]


class PipelineOrchestrator:
    """Production Pipeline Orchestrator for AutoDubStudio."""

    def __init__(self, retry_policy: Optional[RetryPolicy] = None):
        self.retry_policy = retry_policy or RetryPolicy()
        self.executors: Dict[str, BaseStageExecutor] = {
            "INGEST": IngestStageExecutor(),
            "TRANSCRIBE": TranscribeStageExecutor(),
            "TRANSLATE": TranslateStageExecutor(),
            "TTS": TTSStageExecutor(),
            "SUBTITLE": SubtitleStageExecutor(),
            "MIX": MixStageExecutor(),
            "RENDER": RenderStageExecutor(),
            "VALIDATE": ValidateStageExecutor(),
        }

    def calculate_overall_progress(self, completed_stages: List[str], current_stage: str, stage_percent: float) -> float:
        overall = 0.0
        for st in STAGE_SEQUENCE:
            weight = STAGE_WEIGHTS.get(st, 10.0)
            if st in completed_stages:
                overall += weight
            elif st == current_stage:
                overall += (stage_percent / 100.0) * weight
        return min(100.0, max(0.0, round(overall, 1)))

    def _get_checkpoint_file(self, ctx: PipelineContext) -> Path:
        return ctx.project.project_dir / "output" / "pipeline.partial.json"

    def load_checkpoint(self, ctx: PipelineContext) -> Dict[str, Any]:
        chk_file = self._get_checkpoint_file(ctx)
        if not chk_file.exists():
            return {}
        try:
            with open(chk_file, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return {}

    def save_checkpoint(self, ctx: PipelineContext, completed_stages: List[str], current_stage: str, status: str) -> None:
        chk_file = self._get_checkpoint_file(ctx)
        data = {
            "job_id": ctx.job.job_id,
            "pipeline_version": ctx.job.pipeline_version,
            "config_hash": ctx.job.config_hash,
            "completed_stages": completed_stages,
            "current_stage": current_stage,
            "status": status,
            "updated_at": time.time(),
        }
        atomic_write_json(chk_file, data)

    def run_pipeline(self, ctx: PipelineContext, force: bool = False) -> None:
        logger.info(f"[ORCHESTRATOR] Starting pipeline execution for job '{ctx.job.job_id}'...")

        checkpoint = self.load_checkpoint(ctx)
        old_hash = checkpoint.get("config_hash", "")
        completed_stages: List[str] = checkpoint.get("completed_stages", [])

        # Dependency-aware invalidation if config changed
        if old_hash and old_hash != ctx.job.config_hash and not force:
            logger.info(f"[ORCHESTRATOR] Config hash changed ({old_hash[:8]} -> {ctx.job.config_hash[:8]}). Invalidating downstream stages.")
            completed_stages.clear()

        ctx.job.transition_to(JobState.RUNNING.value, force=True)

        for stage_name in STAGE_SEQUENCE:
            if ctx.is_cancelled():
                ctx.job.transition_to(JobState.CANCELLED.value, error_message="Pipeline cancelled by user.")
                self.save_checkpoint(ctx, completed_stages, stage_name, JobState.CANCELLED.value)
                raise PipelineCancelledError("Pipeline cancelled by user.")

            executor = self.executors[stage_name]
            ctx.job.current_stage = stage_name

            # Check if stage can be skipped
            if not force and stage_name in completed_stages and executor.can_skip(ctx):
                logger.info(f"[ORCHESTRATOR] Skipping already completed valid stage '{stage_name}'.")
                overall_p = self.calculate_overall_progress(completed_stages, stage_name, 100.0)
                ctx.job.progress = overall_p
                ctx.emit_progress(stage_name, 100.0, overall_p, f"Stage '{stage_name}' skipped (cached).")
                continue

            # Execute stage
            logger.info(f"[ORCHESTRATOR] Executing stage '{stage_name}'...")
            overall_start_p = self.calculate_overall_progress(completed_stages, stage_name, 0.0)
            ctx.job.progress = overall_start_p
            ctx.emit_progress(stage_name, 0.0, overall_start_p, f"Stage '{stage_name}' started.")

            attempt = 0
            success = False
            last_err: Optional[Exception] = None

            while attempt < self.retry_policy.max_retries and not success:
                attempt += 1
                try:
                    if ctx.is_cancelled():
                        raise PipelineCancelledError("Pipeline cancelled by user.")

                    executor.execute(ctx)
                    executor.validate(ctx)
                    success = True
                except Exception as e:
                    last_err = e
                    logger.warning(f"[ORCHESTRATOR] Stage '{stage_name}' failed on attempt {attempt}: {e}")
                    if self.retry_policy.should_retry(e, attempt):
                        delay = self.retry_policy.calculate_backoff_delay(attempt)
                        logger.info(f"[ORCHESTRATOR] Retrying stage '{stage_name}' in {delay:.1f}s...")
                        time.sleep(delay)
                    else:
                        break

            if not success:
                err_msg = f"Stage '{stage_name}' failed after {attempt} attempts: {last_err}"
                ctx.job.transition_to(JobState.FAILED.value, error_message=err_msg)
                self.save_checkpoint(ctx, completed_stages, stage_name, JobState.FAILED.value)
                raise StageExecutionError(err_msg)

            if stage_name not in completed_stages:
                completed_stages.append(stage_name)

            overall_done_p = self.calculate_overall_progress(completed_stages, stage_name, 100.0)
            ctx.job.progress = overall_done_p
            ctx.emit_progress(stage_name, 100.0, overall_done_p, f"Stage '{stage_name}' completed.")
            self.save_checkpoint(ctx, completed_stages, stage_name, JobState.RUNNING.value)

        ctx.job.progress = 100.0
        ctx.job.transition_to(JobState.COMPLETED.value)
        self.save_checkpoint(ctx, completed_stages, "COMPLETED", JobState.COMPLETED.value)
        logger.info(f"[ORCHESTRATOR] Pipeline execution completed successfully for job '{ctx.job.job_id}'.")
