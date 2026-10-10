import shutil
import tempfile
import time
import unittest
from pathlib import Path

from autodub.jobs.job_manager import JobManager
from autodub.workers.worker_pool import WorkerPool
from autodub.jobs.job_state import JobState
from autodub.models.project import Project


class TestPhase9ConcurrencyAndWorkerPool(unittest.TestCase):

    def setUp(self):
        self.temp_dir = tempfile.mkdtemp(prefix="autodub_test_conc_")
        self.db_path = Path(self.temp_dir) / "conc_jobs.db"
        self.lock_dir = Path(self.temp_dir) / "locks"
        self.job_mgr = JobManager(db_path=self.db_path, lock_dir=self.lock_dir)

    def tearDown(self):
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_01_worker_pool_lifecycle(self):
        pool = WorkerPool(job_manager=self.job_mgr, max_workers=2)
        pool.start()
        self.assertEqual(len(pool.workers), 2)
        pool.stop()
        self.assertEqual(len(pool.workers), 0)

    def test_02_duplicate_job_submission_prevention(self):
        proj_dir = Path(self.temp_dir) / "proj_dup"
        Project(proj_dir, name="proj_dup")

        # Create first job
        j1 = self.job_mgr.create_job(
            project_id=str(proj_dir),
            input_path="in.mp4",
            output_path="out.mp4",
            job_id="j_orig",
            config_hash="same_hash_123"
        )
        j1.transition_to(JobState.QUEUED.value)
        j1.transition_to(JobState.RUNNING.value)
        j1.transition_to(JobState.COMPLETED.value)
        self.job_mgr.store.save_job(j1)

        # Create output file
        out_p = Path("out.mp4")
        out_p.write_bytes(b"MOCK_OUTPUT")

        try:
            # Second submission with same fingerprint
            j2 = self.job_mgr.create_job(
                project_id=str(proj_dir),
                input_path="in.mp4",
                output_path="out.mp4",
                job_id="j_dup",
                config_hash="same_hash_123",
                force_duplicate=False
            )
            # Should return existing completed job
            self.assertEqual(j2.job_id, "j_orig")
        finally:
            out_p.unlink(missing_ok=True)


if __name__ == "__main__":
    unittest.main()
