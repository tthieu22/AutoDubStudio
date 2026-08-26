import shutil
import tempfile
import unittest
from pathlib import Path

from autodub.models.project import Project
from autodub.modules.story_cleaner import StoryCleaner

class TestPhase6StoryCleaner(unittest.TestCase):
    def setUp(self):
        self.test_dir = Path(tempfile.mkdtemp(prefix="autodub_p6_test_"))
        self.project_dir = self.test_dir / "story_clean_proj"
        self.project = Project(self.project_dir, name="clean_test", mode="MODE_STORY")
        self.story_dir = self.project_dir / "story"
        self.story_dir.mkdir(parents=True, exist_ok=True)

    def tearDown(self):
        if self.test_dir.exists():
            shutil.rmtree(self.test_dir, ignore_errors=True)

    def test_01_gutenberg_cleaning(self):
        raw = """The Project Gutenberg eBook of Sample Book
*** START OF THE PROJECT GUTENBERG EBOOK SAMPLE ***
Chapter 1
Once upon a time in a dark wood.

*** END OF THE PROJECT GUTENBERG EBOOK SAMPLE ***
Legal copyright notices follow here..."""
        
        cleaned = StoryCleaner.clean_gutenberg_text(raw)
        self.assertNotIn("START OF THE PROJECT GUTENBERG", cleaned)
        self.assertNotIn("END OF THE PROJECT GUTENBERG", cleaned)
        self.assertIn("Once upon a time in a dark wood.", cleaned)

    def test_02_wikitext_cleaning(self):
        raw = """== Chương 1: Bắt Đầu ==
[[File:Sample.jpg|thumb|Caption]]
[[Category:Truyện cổ]]
{{Template_Banner}}
[[A Lăng|Liêu Trai]] bước vào làng."""

        cleaned = StoryCleaner.clean_wikitext(raw)
        self.assertNotIn("[[File:", cleaned)
        self.assertNotIn("[[Category:", cleaned)
        self.assertNotIn("{{Template_Banner}}", cleaned)
        self.assertIn("Chương 1: Bắt Đầu", cleaned)
        self.assertIn("Liêu Trai bước vào làng.", cleaned)

    def test_03_project_story_cleaning_integration(self):
        self.project.data["story"] = {
            "source_type": "gutenberg",
            "status": "FETCHED"
        }
        self.project.save()

        raw = "*** START OF THIS PROJECT GUTENBERG EBOOK SAMPLE ***\nChapter 1\nA story about a brave knight.\n*** END OF THIS PROJECT GUTENBERG EBOOK ***"
        (self.story_dir / "original.txt").write_text(raw, encoding="utf-8")

        cleaner = StoryCleaner()
        result = cleaner.clean_project_story(self.project)

        cleaned_file = self.story_dir / "cleaned.txt"
        self.assertTrue(cleaned_file.exists())
        self.assertIn("A story about a brave knight.", result)
        self.assertEqual(self.project.data["story"]["status"], "CLEANED")

if __name__ == "__main__":
    unittest.main()
