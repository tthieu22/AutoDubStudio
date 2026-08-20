import shutil
import tempfile
import unittest
from pathlib import Path

from autodub.jobs.job import Job
from autodub.jobs.job_state import JobState
from autodub.jobs.job_store import JobStore
from autodub.jobs.job_lock import JobLock
from autodub.jobs.job_recovery import JobRecovery
from autodub.models.project import Project


class TestPhase9Recovery(unittest.TestCase):

    def setUp(self):
        self.temp_dir = tempfile.mkdtemp(prefix="autodub_test_rec_")
        self.store = JobStore(db_path=Path(self.temp_dir) / "rec_jobs.db")
        self.lock_mgr = JobLock(lock_dir=Path(self.temp_dir) / "locks", stale_timeout_sec=0.1)
        self.recovery = JobRecovery(store=self.store, lock_manager=self.lock_mgr)

    def tearDown(self):
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_01_recover_interrupted_running_job(self):
        proj_dir = Path(self.temp_dir) / "proj_rec"
        Project(proj_dir, name="proj_rec")

        job = Job.create(str(proj_dir), "in.mp4", "out.mp4", job_id="rec_job_1")
        job.transition_to(JobState.QUEUED.value)
        job.transition_to(JobState.RUNNING.value)
        self.store.save_job(job)

        recovered = self.recovery.recover_all()
        self.assertEqual(len(recovered), 1)
        self.assertEqual(recovered[0].job_id, "rec_job_1")
        self.assertEqual(recovered[0].status, JobState.QUEUED.value)

    def test_02_skip_locked_active_job(self):
        proj_dir = Path(self.temp_dir) / "proj_active"
        Project(proj_dir, name="proj_active")

        job = Job.create(str(proj_dir), "in.mp4", "out.mp4", job_id="active_job")
        job.transition_to(JobState.QUEUED.value)
        job.transition_to(JobState.RUNNING.value)
        self.store.save_job(job)

        # Lock the job actively
        self.lock_mgr.acquire("active_job", "live-worker-1")

        recovered = self.recovery.recover_all()
        self.assertEqual(len(recovered), 0)  # Active job skipped from recovery


if __name__ == "__main__":
    unittest.main()
