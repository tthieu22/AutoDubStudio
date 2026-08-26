import json
import shutil
import tempfile
import unittest
from pathlib import Path

from autodub.models.project import Project
from autodub.modules.story_renderer import StoryRenderer
from autodub.modules.final_qa import FinalQAChecker

class TestPhase18To20RenderQA(unittest.TestCase):
    def setUp(self):
        self.test_dir = Path(tempfile.mkdtemp(prefix="autodub_p18_test_"))
        self.project_dir = self.test_dir / "render_proj"
        self.project = Project(self.project_dir, name="render_test", mode="MODE_STORY")
        self.project.data["timeline"] = {"total_duration": 4.0}

    def tearDown(self):
        if self.test_dir.exists():
            shutil.rmtree(self.test_dir, ignore_errors=True)

    def test_01_preview_rendering(self):
        renderer = StoryRenderer(self.project)
        preview_file = renderer.render_preview(self.project)

        self.assertTrue(preview_file.exists())
        self.assertEqual(preview_file.name, "preview.mp4")
        self.assertGreater(preview_file.stat().st_size, 0)

    def test_02_final_rendering(self):
        renderer = StoryRenderer(self.project)
        final_file = renderer.render_final(self.project)

        self.assertTrue(final_file.exists())
        self.assertEqual(final_file.name, "final.mp4")
        self.assertGreater(final_file.stat().st_size, 0)
        self.assertEqual(self.project.data["story"]["status"], "RENDERED")

    def test_03_final_qa_check(self):
        renderer = StoryRenderer(self.project)
        renderer.render_final(self.project)

        qa = FinalQAChecker(self.project)
        report = qa.run_qa()

        self.assertEqual(report["overall_status"], "PASS")
        self.assertTrue((self.project_dir / "reviews" / "final_qa_report.json").exists())

if __name__ == "__main__":
    unittest.main()
