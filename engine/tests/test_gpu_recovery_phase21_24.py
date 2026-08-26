import shutil
import tempfile
import unittest
from pathlib import Path

from autodub.models.project import Project
from autodub.utils.gpu_monitor import GPUMonitor
from autodub.pipeline.recovery import StoryPipelineRecovery

class TestPhase21To24GPURecovery(unittest.TestCase):
    def setUp(self):
        self.test_dir = Path(tempfile.mkdtemp(prefix="autodub_p21_test_"))
        self.project_dir = self.test_dir / "recovery_proj"
        self.project = Project(self.project_dir, name="recovery_test", mode="MODE_STORY")
        from autodub.utils.files import ensure_project_structure
        ensure_project_structure(self.project_dir)

    def tearDown(self):
        if self.test_dir.exists():
            shutil.rmtree(self.test_dir, ignore_errors=True)

    def test_01_gpu_monitor(self):
        info = GPUMonitor.get_vram_info()
        self.assertIn("available", info)
        self.assertIn("free_mb", info)
        safety = GPUMonitor.check_vram_safety(min_free_mb=100)
        self.assertIsInstance(safety, bool)

    def test_02_recovery_scan_fresh_project(self):
        rec = StoryPipelineRecovery(self.project)
        state = rec.scan_recovery_state()

        self.assertFalse(state["story_fetched"])
        self.assertEqual(state["next_action"], "FETCH_STORY")

    def test_03_recovery_scan_partial_state(self):
        (self.project_dir / "story" / "original.txt").write_text("Original text", encoding="utf-8")
        (self.project_dir / "story" / "cleaned.txt").write_text("Cleaned text", encoding="utf-8")
        (self.project_dir / "characters" / "characters.json").write_text("[]", encoding="utf-8")

        rec = StoryPipelineRecovery(self.project)
        state = rec.scan_recovery_state()

        self.assertTrue(state["characters_analyzed"])
        self.assertEqual(state["next_action"], "PLAN_SCENES")

if __name__ == "__main__":
    unittest.main()
