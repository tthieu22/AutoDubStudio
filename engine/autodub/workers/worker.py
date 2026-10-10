import logging
import os
import threading
import time
from pathlib import Path
from typing import Optional, Callable

from autodub.models.project import Project
from autodub.jobs.job import Job
from autodub.jobs.job_state import JobState
from autodub.jobs.job_manager import JobManager
from autodub.orchestration.pipeline_context import PipelineContext
from autodub.orchestration.orchestrator import PipelineOrchestrator
from autodub.exceptions import PipelineCancelledError

logger = logging.getLogger("autodub.workers.worker")


class Worker(threading.Thread):
    """Background worker thread processing jobs from JobManager queue."""

    def __init__(
        self,
        worker_id: str,
        job_manager: JobManager,
        orchestrator: Optional[PipelineOrchestrator] = None,
        poll_interval_sec: float = 1.0,
    ):
        super().__init__(name=f"WorkerThread-{worker_id}", daemon=True)
        self.worker_id = worker_id
        self.job_manager = job_manager
        self.orchestrator = orchestrator or PipelineOrchestrator()
        self.poll_interval_sec = poll_interval_sec
        self._stop_event = threading.Event()
        self.current_job: Optional[Job] = None

    def stop(self) -> None:
        self._stop_event.set()

    @property
    def is_stopped(self) -> bool:
        return self._stop_event.is_set()

    def run(self) -> None:
        logger.info(f"[WORKER {self.worker_id}] Worker started.")

        while not self._stop_event.is_set():
            job = self.job_manager.dequeue_job(self.worker_id)
            if not job:
                time.sleep(self.poll_interval_sec)
                continue

            self.current_job = job
            job_id = job.job_id

            # Acquire atomic job lock
            if not self.job_manager.lock_manager.acquire(job_id, self.worker_id):
                logger.warning(f"[WORKER {self.worker_id}] Could not acquire lock for job '{job_id}'. Skipping.")
                self.current_job = None
                continue

            try:
                logger.info(f"[WORKER {self.worker_id}] Processing job '{job_id}' (Project: {job.project_id})...")

                proj_dir = Path(job.project_id)
                if not proj_dir.is_absolute():
                    workspace_env = os.environ.get("AUTODUB_WORKSPACE")
                    base_dir = Path(workspace_env) if workspace_env else (Path.cwd() / "projects")
                    proj_dir = base_dir / job.project_id

                project = Project(proj_dir)

                def is_cancelled_check() -> bool:
                    if self._stop_event.is_set():
                        return True
                    latest = self.job_manager.get_job(job_id)
                    return latest.status in (JobState.CANCEL_REQUESTED.value, JobState.CANCELLED.value) if latest else False

                def progress_cb(evt: dict) -> None:
                    # Update job state in store
                    job.progress = evt.get("overall_percent", job.progress)
                    job.current_stage = evt.get("stage", job.current_stage)
                    self.job_manager.store.save_job(job)
                    self.job_manager.store.log_event(job_id, "PROGRESS", job.current_stage, evt.get("message", ""))

                ctx = PipelineContext(
                    job=job,
                    project=project,
                    config=project.data,
                    workspace=proj_dir,
                    is_cancelled=is_cancelled_check,
                    progress_callback=progress_cb,
                )

                self.orchestrator.run_pipeline(ctx)
                self.job_manager.store.save_job(job)
                self.job_manager.store.log_event(job_id, "JOB_COMPLETED", "VALIDATE", "Job completed successfully.")

            except PipelineCancelledError:
                logger.info(f"[WORKER {self.worker_id}] Job '{job_id}' execution cancelled.")
                job.transition_to(JobState.CANCELLED.value, error_message="Job cancelled by user.")
                self.job_manager.store.save_job(job)
                self.job_manager.store.log_event(job_id, "JOB_CANCELLED", job.current_stage, "Job cancelled by user.")

            except Exception as e:
                logger.error(f"[WORKER {self.worker_id}] Job '{job_id}' failed: {e}")
                if job.retry_count < job.max_retries:
                    self.job_manager.retry_job(job_id)
                else:
                    job.transition_to(JobState.FAILED.value, error_message=str(e))
                    self.job_manager.store.save_job(job)
                    self.job_manager.store.log_event(job_id, "JOB_FAILED", job.current_stage, str(e))

            finally:
                self.job_manager.lock_manager.release(job_id, self.worker_id)
                self.current_job = None

        logger.info(f"[WORKER {self.worker_id}] Worker stopped.")
