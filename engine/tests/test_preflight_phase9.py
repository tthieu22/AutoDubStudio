import shutil
import tempfile
import unittest
from pathlib import Path

from autodub.pipeline.manager import PipelineManager
from autodub.exceptions import AutoDubError


class TestPhase9Preflight(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.mkdtemp(prefix="autodub_test_prf_p9_")
        self.proj_dir = Path(self.temp_dir) / "test_preflight_project"
        self.proj_dir.mkdir(parents=True, exist_ok=True)

    def tearDown(self):
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_01_preflight_missing_input_video(self):
        mgr = PipelineManager(str(self.proj_dir))
        with self.assertRaises(AutoDubError) as ctx:
            mgr.preflight_check(strict=True)
        self.assertIn("does not exist", str(ctx.exception))
