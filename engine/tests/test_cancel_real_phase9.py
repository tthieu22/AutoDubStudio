import shutil
import tempfile
import unittest
from pathlib import Path

from autodub.pipeline.manager import PipelineManager
from autodub.exceptions import PipelineCancelledError


class TestPhase9CancelReal(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.mkdtemp(prefix="autodub_test_can_p9_")
        self.proj_dir = Path(self.temp_dir) / "test_cancel_project"
        self.proj_dir.mkdir(parents=True, exist_ok=True)

    def tearDown(self):
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_01_cancellation_flag_handling(self):
        mgr = PipelineManager(str(self.proj_dir))
        self.assertFalse(mgr.is_cancelled())

        mgr.cancel()
        self.assertTrue(mgr.is_cancelled())
