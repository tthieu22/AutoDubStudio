import json
import shutil
import tempfile
import unittest
from pathlib import Path

from autodub.models.project import Project
from autodub.modules.story_analyzer import StoryAnalyzer

class TestPhase7StoryAnalyzer(unittest.TestCase):
    def setUp(self):
        self.test_dir = Path(tempfile.mkdtemp(prefix="autodub_p7_test_"))
        self.project_dir = self.test_dir / "story_analyze_proj"
        self.project = Project(self.project_dir, name="analyze_test", mode="MODE_STORY")
        self.story_dir = self.project_dir / "story"
        self.story_dir.mkdir(parents=True, exist_ok=True)

    def tearDown(self):
        if self.test_dir.exists():
            shutil.rmtree(self.test_dir, ignore_errors=True)

    def test_01_chapter_splitting(self):
        analyzer = StoryAnalyzer()
        story_text = """Chương 1: Đêm Mưa Ở Làng Cổ
A Lăng bước đi dưới cơn mưa rừng tăm tối.

Chương 2: Bí Mật Trong Đền
Cô gái mang chiếc đèn lồng đỏ quay đầu nhìn A Lăng."""

        chapters = analyzer.split_chapters(story_text)
        self.assertEqual(len(chapters), 2)
        self.assertIn("Chương 1", chapters[0]["title"])
        self.assertIn("Chương 2", chapters[1]["title"])

    def test_02_project_analysis_integration(self):
        cleaned_text = """Chương 1: Khởi Đầu
Ngày xửa ngày xưa, ở một ngôi làng cổ có người thợ săn tên A Lăng."""
        (self.story_dir / "cleaned.txt").write_text(cleaned_text, encoding="utf-8")

        analyzer = StoryAnalyzer()
        res = analyzer.analyze_project_story(self.project)

        self.assertTrue((self.project_dir / "characters" / "characters.json").exists())
        self.assertTrue((self.project_dir / "story" / "world.json").exists())
        self.assertTrue((self.project_dir / "timeline" / "timeline.json").exists())
        self.assertTrue((self.project_dir / "story" / "chapters" / "chapter_001.txt").exists())

        self.assertEqual(self.project.data["story"]["status"], "ANALYZED")

if __name__ == "__main__":
    unittest.main()
