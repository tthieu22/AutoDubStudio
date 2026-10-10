import json
import logging
from pathlib import Path
from typing import List, Dict, Any

from autodub.jobs.job import Job
from autodub.jobs.job_state import JobState
from autodub.jobs.job_store import JobStore
from autodub.jobs.job_lock import JobLock

logger = logging.getLogger("autodub.jobs.recovery")


class JobRecovery:
    """Startup & manual recovery engine for interrupted or orphaned jobs."""

    def __init__(self, store: JobStore, lock_manager: JobLock):
        self.store = store
        self.lock_manager = lock_manager

    def recover_all(self) -> List[Job]:
        """Scan and recover all orphaned RUNNING/RECOVERING jobs."""
        interrupted_jobs = self.store.list_jobs(status=JobState.RUNNING.value, limit=500)
        recovering_jobs = self.store.list_jobs(status=JobState.RECOVERING.value, limit=500)

        candidates = {j.job_id: j for j in interrupted_jobs + recovering_jobs}
        recovered: List[Job] = []

        for job_id, job in candidates.items():
            # If job is locked and lock is fresh, a worker is actively processing it
            if self.lock_manager.is_locked(job_id):
                logger.info(f"[RECOVERY] Skipping job '{job_id}' - actively locked by a live worker.")
                continue

            try:
                job.transition_to(JobState.RECOVERING.value, force=True)
                self.store.save_job(job)
                self.store.log_event(job_id, "JOB_RECOVERING", job.current_stage, "Interrupted job flagged for recovery.")

                # Validate project directory checkpoint
                proj_dir = Path(job.project_id)
                if not proj_dir.is_absolute():
                    proj_dir = Path.cwd() / job.project_id

                partial_file = proj_dir / "output" / "pipeline.partial.json"
                if partial_file.exists():
                    try:
                        with open(partial_file, "r", encoding="utf-8") as f:
                            pdata = json.load(f)
                        completed_stages = pdata.get("completed_stages", [])
                        current_stage = pdata.get("current_stage", "INGEST")
                        if completed_stages:
                            job.current_stage = current_stage
                    except Exception as e:
                        logger.warning(f"[RECOVERY] Failed reading partial checkpoint for '{job_id}': {e}")

                job.transition_to(JobState.QUEUED.value, force=True)
                self.store.save_job(job)
                self.store.log_event(job_id, "JOB_RECOVERED", job.current_stage, "Interrupted job recovered and re-queued.")
                recovered.append(job)

            except Exception as e:
                logger.error(f"[RECOVERY] Failed to recover job '{job_id}': {e}")
                job.transition_to(JobState.FAILED.value, force=True, error_message=f"Recovery failed: {e}")
                self.store.save_job(job)
                self.store.log_event(job_id, "JOB_FAILED", job.current_stage, f"Recovery failed: {e}")

        return recovered
