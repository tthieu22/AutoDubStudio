import shutil
import tempfile
import time
import unittest
from pathlib import Path

from autodub.jobs.job_lock import JobLock


class TestPhase9JobLock(unittest.TestCase):

    def setUp(self):
        self.temp_dir = tempfile.mkdtemp(prefix="autodub_test_lock_")
        self.lock_dir = Path(self.temp_dir) / "locks"
        self.lock_mgr = JobLock(lock_dir=self.lock_dir, stale_timeout_sec=0.5)

    def tearDown(self):
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_01_acquire_and_release(self):
        acquired = self.lock_mgr.acquire("job_100", "worker-1")
        self.assertTrue(acquired)
        self.assertTrue(self.lock_mgr.is_locked("job_100"))

        released = self.lock_mgr.release("job_100", "worker-1")
        self.assertTrue(released)
        self.assertFalse(self.lock_mgr.is_locked("job_100"))

    def test_02_lock_collision(self):
        acquired1 = self.lock_mgr.acquire("job_100", "worker-1")
        self.assertTrue(acquired1)

        acquired2 = self.lock_mgr.acquire("job_100", "worker-2")
        self.assertFalse(acquired2)

    def test_03_stale_lock_recovery(self):
        acquired1 = self.lock_mgr.acquire("job_100", "worker-1")
        self.assertTrue(acquired1)

        # Wait for stale timeout (0.5s)
        time.sleep(0.6)

        acquired2 = self.lock_mgr.acquire("job_100", "worker-2")
        self.assertTrue(acquired2)


if __name__ == "__main__":
    unittest.main()
