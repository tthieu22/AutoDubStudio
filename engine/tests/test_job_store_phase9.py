import unittest
import shutil
import tempfile
from pathlib import Path

from autodub.jobs.job import Job
from autodub.jobs.job_state import JobState
from autodub.jobs.job_store import JobStore
from autodub.exceptions import JobAlreadyExistsError


class TestPhase9JobStore(unittest.TestCase):

    def setUp(self):
        self.temp_dir = tempfile.mkdtemp(prefix="autodub_test_store_")
        self.db_path = Path(self.temp_dir) / "test_jobs.db"
        self.store = JobStore(db_path=self.db_path)

    def tearDown(self):
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_01_save_and_get_job(self):
        job = Job.create("p1", "in.mp4", "out.mp4", job_id="job_001")
        self.store.save_job(job)

        retrieved = self.store.get_job("job_001")
        self.assertIsNotNone(retrieved)
        self.assertEqual(retrieved.job_id, "job_001")
        self.assertEqual(retrieved.project_id, "p1")

    def test_02_create_only_constraint(self):
        job = Job.create("p1", "in.mp4", "out.mp4", job_id="job_001")
        self.store.save_job(job)

        with self.assertRaises(JobAlreadyExistsError):
            self.store.save_job(job, create_only=True)

    def test_03_find_by_fingerprint(self):
        job = Job.create("p1", "in.mp4", "out.mp4", job_id="job_001", config_hash="abc123hash")
        job.transition_to(JobState.QUEUED.value)
        job.transition_to(JobState.RUNNING.value)
        job.transition_to(JobState.COMPLETED.value)
        self.store.save_job(job)

        found = self.store.find_job_by_fingerprint("in.mp4", "abc123hash")
        self.assertIsNotNone(found)
        self.assertEqual(found.job_id, "job_001")

    def test_04_list_jobs_by_status(self):
        j1 = Job.create("p1", "in1.mp4", "out1.mp4", job_id="j1")
        j2 = Job.create("p2", "in2.mp4", "out2.mp4", job_id="j2")
        self.store.save_job(j1)
        self.store.save_job(j2)

        j2.transition_to(JobState.QUEUED.value)
        self.store.save_job(j2)

        pending = self.store.list_jobs(status="PENDING")
        queued = self.store.list_jobs(status="QUEUED")

        self.assertEqual(len(pending), 1)
        self.assertEqual(pending[0].job_id, "j1")
        self.assertEqual(len(queued), 1)
        self.assertEqual(queued[0].job_id, "j2")

    def test_05_log_and_get_events(self):
        job = Job.create("p1", "in.mp4", "out.mp4", job_id="job_evt")
        self.store.save_job(job)

        self.store.log_event("job_evt", "JOB_CREATED", "INGEST", "Job initialized", {"foo": "bar"})
        events = self.store.get_job_events("job_evt")

        self.assertEqual(len(events), 1)
        self.assertEqual(events[0]["event_type"], "JOB_CREATED")
        self.assertEqual(events[0]["metadata"], {"foo": "bar"})

    def test_06_delete_job(self):
        job = Job.create("p1", "in.mp4", "out.mp4", job_id="del_1")
        self.store.save_job(job)

        deleted = self.store.delete_job("del_1")
        self.assertTrue(deleted)
        self.assertIsNone(self.store.get_job("del_1"))


if __name__ == "__main__":
    unittest.main()
