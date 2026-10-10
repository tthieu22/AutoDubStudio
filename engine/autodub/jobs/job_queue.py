import threading
from typing import Optional, List
from autodub.jobs.job import Job
from autodub.jobs.job_state import JobState
from autodub.jobs.job_store import JobStore
from autodub.exceptions import QueueError, JobNotFoundError


class JobQueue:
    """Persistent FIFO / Priority Queue backed by JobStore."""

    def __init__(self, job_store: JobStore):
        self.store = job_store
        self._lock = threading.Lock()

    def enqueue(self, job_id: str, priority: Optional[int] = None) -> Job:
        with self._lock:
            job = self.store.get_job(job_id)
            if not job:
                raise JobNotFoundError(f"Cannot enqueue missing job '{job_id}'.")

            if priority is not None:
                job.priority = priority

            job.transition_to(JobState.QUEUED.value)
            self.store.save_job(job)
            self.store.log_event(job_id, "JOB_QUEUED", job.current_stage, f"Job queued with priority {job.priority}.")
            return job

    def dequeue(self, worker_id: str) -> Optional[Job]:
        with self._lock:
            queued_jobs = self.store.list_jobs(status=JobState.QUEUED.value, limit=1)
            if not queued_jobs:
                return None

            job = queued_jobs[0]
            job.worker_id = worker_id
            job.transition_to(JobState.RUNNING.value)
            self.store.save_job(job)
            self.store.log_event(
                job.job_id, "JOB_STARTED", job.current_stage, f"Job dequeued and assigned to worker '{worker_id}'."
            )
            return job

    def peek(self) -> Optional[Job]:
        with self._lock:
            queued_jobs = self.store.list_jobs(status=JobState.QUEUED.value, limit=1)
            return queued_jobs[0] if queued_jobs else None

    def get_queue_length(self) -> int:
        with self._lock:
            queued = self.store.list_jobs(status=JobState.QUEUED.value, limit=1000)
            return len(queued)

    def clear(self) -> int:
        with self._lock:
            queued = self.store.list_jobs(status=JobState.QUEUED.value, limit=1000)
            count = 0
            for job in queued:
                job.transition_to(JobState.CANCELLED.value, error_message="Queue cleared.")
                self.store.save_job(job)
                self.store.log_event(job.job_id, "JOB_CANCELLED", job.current_stage, "Cancelled due to queue clear.")
                count += 1
            return count
