import logging
import time
from typing import List, Optional

from autodub.jobs.job_manager import JobManager
from autodub.workers.worker import Worker
from autodub.orchestration.orchestrator import PipelineOrchestrator

logger = logging.getLogger("autodub.workers.pool")


class WorkerPool:
    """Manager for a pool of worker threads with resource-aware concurrency."""

    def __init__(
        self,
        job_manager: JobManager,
        max_workers: int = 2,
        orchestrator: Optional[PipelineOrchestrator] = None,
    ):
        self.job_manager = job_manager
        self.max_workers = max(1, max_workers)
        self.orchestrator = orchestrator or PipelineOrchestrator()
        self.workers: List[Worker] = []
        self._is_running = False

    def start(self) -> None:
        if self._is_running:
            return

        self._is_running = True
        logger.info(f"[WORKER_POOL] Starting worker pool with {self.max_workers} workers...")

        # Run startup recovery on job store before spawning workers
        self.job_manager.recover_jobs()

        for i in range(self.max_workers):
            w_id = f"worker-{i+1:02d}"
            worker = Worker(
                worker_id=w_id,
                job_manager=self.job_manager,
                orchestrator=self.orchestrator,
            )
            self.workers.append(worker)
            worker.start()

    def stop(self, timeout_sec: float = 10.0) -> None:
        if not self._is_running:
            return

        logger.info("[WORKER_POOL] Stopping worker pool...")
        for w in self.workers:
            w.stop()

        start_wait = time.time()
        for w in self.workers:
            rem = max(0.1, timeout_sec - (time.time() - start_wait))
            w.join(timeout=rem)

        self.workers.clear()
        self._is_running = False
        logger.info("[WORKER_POOL] Worker pool stopped.")

    @property
    def active_worker_count(self) -> int:
        return sum(1 for w in self.workers if w.is_alive() and w.current_job is not None)
