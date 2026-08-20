import json
import shutil
import tempfile
import unittest
from pathlib import Path

from autodub.jobs.job_manager import JobManager
from autodub.jobs.job import Job


class TestPhase9CLI(unittest.TestCase):

    def setUp(self):
        self.temp_dir = tempfile.mkdtemp(prefix="autodub_test_cli9_")
        self.db_path = Path(self.temp_dir) / "cli_jobs.db"
        self.job_mgr = JobManager(db_path=self.db_path)

    def tearDown(self):
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_01_job_manager_cli_actions(self):
        job = self.job_mgr.create_job("p1", "in.mp4", "out.mp4", job_id="cli_j1")
        self.assertEqual(job.job_id, "cli_j1")

        listed = self.job_mgr.list_jobs()
        self.assertEqual(len(listed), 1)

        paused = self.job_mgr.pause_job("cli_j1")
        self.assertEqual(paused.status, "PAUSED")

        resumed = self.job_mgr.resume_job("cli_j1")
        self.assertEqual(resumed.status, "QUEUED")

        cancelled = self.job_mgr.cancel_job("cli_j1")
        self.assertEqual(cancelled.status, "CANCELLED")

        cleaned = self.job_mgr.clean_jobs()
        self.assertEqual(cleaned, 1)
        self.assertEqual(len(self.job_mgr.list_jobs()), 0)


if __name__ == "__main__":
    unittest.main()
