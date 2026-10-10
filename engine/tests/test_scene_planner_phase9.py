import json
import shutil
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from autodub.models.project import Project
from autodub.modules.scene_planner import ScenePlanner
from autodub.pipeline.task_state import TaskStatus

class TestPhase9ScenePlanner(unittest.TestCase):
    def setUp(self):
        self.test_dir = Path(tempfile.mkdtemp(prefix="autodub_p9_test_"))
        self.project_dir = self.test_dir / "story_scene_proj"
        self.project = Project(self.project_dir, name="scene_test", mode="MODE_STORY")
        
        # Setup chapter file
        chap_dir = self.project_dir / "story" / "chapters"
        chap_dir.mkdir(parents=True, exist_ok=True)
        (chap_dir / "chapter_001.txt").write_text("Chương 1\nĐêm đó mưa rất to.\nA Lăng mang đèn lồng ra cổng.", encoding="utf-8")

    def tearDown(self):
        if self.test_dir.exists():
            shutil.rmtree(self.test_dir, ignore_errors=True)

    @patch.object(ScenePlanner, "_call_qwen_json")
    def test_01_scene_planning_with_mock_qwen(self, mock_qwen):
        mock_qwen.return_value = [
            {
                "scene_index": 1,
                "speaker": "NARRATOR",
                "narration": "Đêm đó mưa rất to.",
                "visual_prompt": "dark rainy night village",
                "duration": 8
            },
            {
                "scene_index": 2,
                "speaker": "A_LANG",
                "narration": "A Lăng mang đèn lồng ra cổng.",
                "visual_prompt": "man holding red lantern in rain",
                "duration": 6
            }
        ]

        planner = ScenePlanner()
        scenes = planner.plan_chapter_scenes(self.project, chapter_index=1)

        self.assertEqual(len(scenes), 2)
        self.assertEqual(scenes[0]["id"], "scene_001")
        self.assertEqual(scenes[0]["speaker"], "NARRATOR")
        self.assertEqual(scenes[0]["status"], TaskStatus.REVIEW_REQUIRED.value)

        # Check scene file creation
        scene_001_file = self.project_dir / "scenes" / "scene_001.json"
        self.assertTrue(scene_001_file.exists())
        
        with open(scene_001_file, "r", encoding="utf-8") as f:
            data = json.load(f)
        self.assertEqual(data["visual_prompt"], "dark rainy night village")

if __name__ == "__main__":
    unittest.main()
