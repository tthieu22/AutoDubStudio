import json
import shutil
import tempfile
import unittest
from pathlib import Path

from autodub.models.project import Project
from autodub.modules.sd_image_generator import SDImageGenerator
from autodub.pipeline.task_state import TaskStatus
from autodub.exceptions import AutoDubError

class TestPhase1011SDImageGenerator(unittest.TestCase):
    def setUp(self):
        self.test_dir = Path(tempfile.mkdtemp(prefix="autodub_p10_test_"))
        self.project_dir = self.test_dir / "sd_image_proj"
        self.project = Project(self.project_dir, name="sd_test", mode="MODE_STORY")
        
        self.scene = {
            "id": "scene_001",
            "chapter_index": 1,
            "scene_index": 1,
            "speaker": "NARRATOR",
            "narration": "Đêm đó mưa rất to.",
            "visual_prompt": "dark rainy night in ancient Chinese village",
            "duration": 8,
            "status": TaskStatus.REVIEW_REQUIRED.value,
            "attempt": 1
        }
        
        scene_file = self.project_dir / "scenes" / "scene_001.json"
        scene_file.parent.mkdir(parents=True, exist_ok=True)
        with open(scene_file, "w", encoding="utf-8") as f:
            json.dump(self.scene, f, indent=2, ensure_ascii=False)

    def tearDown(self):
        if self.test_dir.exists():
            shutil.rmtree(self.test_dir, ignore_errors=True)

    def test_01_review_gate_enforcement(self):
        gen = SDImageGenerator(self.project)
        # Should raise AutoDubError because status is REVIEW_REQUIRED and bypass_review=False
        with self.assertRaises(AutoDubError):
            gen.generate_image_for_scene(self.scene, bypass_review=False)

    def test_02_image_generation_with_bypass(self):
        gen = SDImageGenerator(self.project)
        img_path = gen.generate_image_for_scene(self.scene, bypass_review=True)
        
        self.assertTrue(img_path.exists())
        self.assertEqual(img_path.name, "scene_001.png")
        self.assertEqual(self.scene["image_path"], "assets/images/scene_001.png")

    def test_03_regeneration_attempt_limit(self):
        gen = SDImageGenerator(self.project)
        gen.generate_image_for_scene(self.scene, bypass_review=True)

        # Attempt 2
        gen.regenerate_scene_image(self.scene, new_prompt="updated prompt 2")
        self.assertEqual(self.scene["attempt"], 2)

        # Attempt 3
        gen.regenerate_scene_image(self.scene, new_prompt="updated prompt 3")
        self.assertEqual(self.scene["attempt"], 3)

        # Attempt 4 should fail exceeding limit
        with self.assertRaises(AutoDubError):
            gen.regenerate_scene_image(self.scene, new_prompt="attempt 4 fail")

if __name__ == "__main__":
    unittest.main()
