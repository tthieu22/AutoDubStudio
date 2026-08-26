import json
import shutil
import tempfile
import unittest
from pathlib import Path

from autodub.models.project import Project
from autodub.modules.story_memory import StoryMemoryEngine

class TestPhase8StoryMemory(unittest.TestCase):
    def setUp(self):
        self.test_dir = Path(tempfile.mkdtemp(prefix="autodub_p8_test_"))
        self.project_dir = self.test_dir / "story_memory_proj"
        self.project = Project(self.project_dir, name="memory_test", mode="MODE_STORY")
        
        # Setup mock characters & world
        chars = [
            {"name": "A Lăng", "gender": "male", "tone": "Điềm tĩnh", "assigned_voice": "vi_VN-viss-low.onnx"},
            {"name": "Mẫu Đơn", "gender": "female", "tone": "Bí ẩn", "assigned_voice": "vi_VN-viss-low.onnx"}
        ]
        char_file = self.project_dir / "characters" / "characters.json"
        char_file.parent.mkdir(parents=True, exist_ok=True)
        with open(char_file, "w", encoding="utf-8") as f:
            json.dump(chars, f, indent=2, ensure_ascii=False)

        world = {"locations": ["Thôn Sơn Cước"], "era": "Thời Nhà Thanh"}
        world_file = self.project_dir / "story" / "world.json"
        world_file.parent.mkdir(parents=True, exist_ok=True)
        with open(world_file, "w", encoding="utf-8") as f:
            json.dump(world, f, indent=2, ensure_ascii=False)

    def tearDown(self):
        if self.test_dir.exists():
            shutil.rmtree(self.test_dir, ignore_errors=True)

    def test_01_bibles_reading(self):
        memory = StoryMemoryEngine(self.project)
        chars = memory.get_character_bible()
        self.assertEqual(len(chars), 2)
        self.assertEqual(chars[0]["name"], "A Lăng")

        world = memory.get_world_bible()
        self.assertIn("Thôn Sơn Cước", world["locations"])

    def test_02_rolling_summary_update(self):
        memory = StoryMemoryEngine(self.project)
        memory.update_rolling_summary(1, "A Lăng phát hiện chiếc đèn lồng đỏ ở cổng làng.")

        rolling = memory.get_rolling_summary()
        self.assertIn("A Lăng phát hiện chiếc đèn lồng đỏ", rolling)
        self.assertTrue((self.project_dir / "story" / "summaries" / "summary_ch001.txt").exists())

        # Update chapter 2
        memory.update_rolling_summary(2, "Mẫu Đơn xuất hiện và biến mất trong mưa.")
        rolling2 = memory.get_rolling_summary()
        self.assertIn("Chương 1", rolling2)
        self.assertIn("Chương 2", rolling2)

    def test_03_context_prompt_building(self):
        memory = StoryMemoryEngine(self.project)
        memory.update_rolling_summary(1, "Diễn biến chương 1...")
        prompt = memory.build_context_prompt(2, "Nội dung chương 2...")

        self.assertIn("A Lăng", prompt)
        self.assertIn("Thôn Sơn Cước", prompt)
        self.assertIn("Diễn biến chương 1...", prompt)
        self.assertIn("Nội dung chương 2...", prompt)

if __name__ == "__main__":
    unittest.main()
