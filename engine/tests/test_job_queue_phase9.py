import shutil
import tempfile
import unittest
from pathlib import Path

from autodub.jobs.job import Job
from autodub.jobs.job_state import JobState
from autodub.jobs.job_store import JobStore
from autodub.jobs.job_queue import JobQueue


class TestPhase9JobQueue(unittest.TestCase):

    def setUp(self):
        self.temp_dir = tempfile.mkdtemp(prefix="autodub_test_queue_")
        self.store = JobStore(db_path=Path(self.temp_dir) / "queue_jobs.db")
        self.queue = JobQueue(job_store=self.store)

    def tearDown(self):
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_01_enqueue_and_dequeue_fifo(self):
        j1 = Job.create("p1", "in1.mp4", "out1.mp4", job_id="q1", priority=5)
        j2 = Job.create("p2", "in2.mp4", "out2.mp4", job_id="q2", priority=5)
        j1.created_at = 1000.0
        j2.created_at = 2000.0
        self.store.save_job(j1)
        self.store.save_job(j2)

        self.queue.enqueue("q1")
        self.queue.enqueue("q2")

        self.assertEqual(self.queue.get_queue_length(), 2)

        dequeued = self.queue.dequeue("worker-1")
        self.assertIsNotNone(dequeued)
        self.assertEqual(dequeued.job_id, "q1")
        self.assertEqual(dequeued.worker_id, "worker-1")
        self.assertEqual(dequeued.status, JobState.RUNNING.value)

    def test_02_priority_ordering(self):
        j1 = Job.create("p1", "in1.mp4", "out1.mp4", job_id="low_p", priority=1)
        j2 = Job.create("p2", "in2.mp4", "out2.mp4", job_id="high_p", priority=10)
        self.store.save_job(j1)
        self.store.save_job(j2)

        self.queue.enqueue("low_p")
        self.queue.enqueue("high_p")

        dequeued = self.queue.dequeue("worker-1")
        self.assertIsNotNone(dequeued)
        self.assertEqual(dequeued.job_id, "high_p")

    def test_03_peek_queue(self):
        j1 = Job.create("p1", "in1.mp4", "out1.mp4", job_id="q1")
        self.store.save_job(j1)
        self.queue.enqueue("q1")

        peeked = self.queue.peek()
        self.assertIsNotNone(peeked)
        self.assertEqual(peeked.job_id, "q1")
        self.assertEqual(self.queue.get_queue_length(), 1)

    def test_04_clear_queue(self):
        j1 = Job.create("p1", "in1.mp4", "out1.mp4", job_id="q1")
        j2 = Job.create("p2", "in2.mp4", "out2.mp4", job_id="q2")
        self.store.save_job(j1)
        self.store.save_job(j2)
        self.queue.enqueue("q1")
        self.queue.enqueue("q2")

        count = self.queue.clear()
        self.assertEqual(count, 2)
        self.assertEqual(self.queue.get_queue_length(), 0)


if __name__ == "__main__":
    unittest.main()
