from pathlib import Path
from typing import Optional, List, Dict, Any

from autodub.jobs.job import Job
from autodub.jobs.job_state import JobState
from autodub.jobs.job_store import JobStore
from autodub.jobs.job_queue import JobQueue
from autodub.jobs.job_lock import JobLock
from autodub.jobs.job_recovery import JobRecovery
from autodub.exceptions import JobNotFoundError, JobAlreadyExistsError, InvalidJobStateTransitionError


class JobManager:
    """Unified manager for AutoDubStudio Job Store, Queue, Lock, and Recovery."""

    def __init__(self, db_path: Optional[Path] = None, lock_dir: Optional[Path] = None):
        self.store = JobStore(db_path=db_path)
        self.queue = JobQueue(job_store=self.store)
        self.lock_manager = JobLock(lock_dir=lock_dir)
        self.recovery_engine = JobRecovery(store=self.store, lock_manager=self.lock_manager)

    def create_job(
        self,
        project_id: str,
        input_path: str,
        output_path: str,
        *,
        job_id: Optional[str] = None,
        config_hash: str = "",
        priority: int = 5,
        max_retries: int = 3,
        auto_enqueue: bool = True,
        force_duplicate: bool = False
    ) -> Job:
        # Check duplicate fingerprint if not forced
        if not force_duplicate and config_hash:
            existing = self.store.find_job_by_fingerprint(input_path, config_hash)
            if existing and existing.status == JobState.COMPLETED.value:
                # Check output file exists
                out_p = Path(existing.output_path)
                if out_p.exists() and out_p.stat().st_size > 0:
                    return existing

        job = Job.create(
            project_id=project_id,
            input_path=input_path,
            output_path=output_path,
            job_id=job_id,
            config_hash=config_hash,
            priority=priority,
            max_retries=max_retries
        )

        self.store.save_job(job, create_only=True)
        self.store.log_event(job.job_id, "JOB_CREATED", job.current_stage, f"Job created for input '{input_path}'.")

        if auto_enqueue:
            job = self.queue.enqueue(job.job_id, priority=priority)

        return job

    def get_job(self, job_id: str) -> Optional[Job]:
        return self.store.get_job(job_id)

    def list_jobs(self, status: Optional[str] = None, limit: int = 100) -> List[Job]:
        return self.store.list_jobs(status=status, limit=limit)

    def enqueue_job(self, job_id: str, priority: Optional[int] = None) -> Job:
        return self.queue.enqueue(job_id, priority=priority)

    def dequeue_job(self, worker_id: str) -> Optional[Job]:
        return self.queue.dequeue(worker_id)

    def pause_job(self, job_id: str) -> Job:
        job = self.store.get_job(job_id)
        if not job:
            raise JobNotFoundError(f"Job '{job_id}' not found.")

        job.transition_to(JobState.PAUSED.value)
        self.store.save_job(job)
        self.store.log_event(job_id, "JOB_PAUSED", job.current_stage, "Job paused by user.")
        return job

    def resume_job(self, job_id: str) -> Job:
        job = self.store.get_job(job_id)
        if not job:
            raise JobNotFoundError(f"Job '{job_id}' not found.")

        if job.status not in (JobState.PAUSED.value, JobState.FAILED.value, JobState.CANCELLED.value):
            raise InvalidJobStateTransitionError(f"Cannot resume job '{job_id}' in state '{job.status}'.")

        job.transition_to(JobState.QUEUED.value, force=True)
        self.store.save_job(job)
        self.store.log_event(job_id, "JOB_RESUMED", job.current_stage, "Job resumed and re-queued.")
        return job

    def cancel_job(self, job_id: str, reason: str = "Cancelled by user.") -> Job:
        job = self.store.get_job(job_id)
        if not job:
            raise JobNotFoundError(f"Job '{job_id}' not found.")

        if job.status == JobState.RUNNING.value:
            job.transition_to(JobState.CANCEL_REQUESTED.value)
        else:
            job.transition_to(JobState.CANCELLED.value, force=True, error_message=reason)

        self.store.save_job(job)
        self.store.log_event(job_id, "JOB_CANCELLED", job.current_stage, reason)
        return job

    def retry_job(self, job_id: str) -> Job:
        job = self.store.get_job(job_id)
        if not job:
            raise JobNotFoundError(f"Job '{job_id}' not found.")

        job.retry_count += 1
        job.transition_to(JobState.RETRYING.value, force=True)
        self.store.save_job(job)
        self.store.log_event(
            job_id, "RETRY_SCHEDULED", job.current_stage, f"Retry attempt {job.retry_count}/{job.max_retries} scheduled."
        )

        job.transition_to(JobState.QUEUED.value, force=True)
        self.store.save_job(job)
        return job

    def recover_jobs(self) -> List[Job]:
        return self.recovery_engine.recover_all()

    def clean_jobs(self, status: Optional[str] = None) -> int:
        jobs = self.store.list_jobs(status=status, limit=1000)
        count = 0
        for job in jobs:
            if status is None or job.status.upper() == status.upper():
                self.store.delete_job(job.job_id)
                self.lock_manager.release(job.job_id, worker_id=job.worker_id or "", force=True)
                count += 1
        return count
