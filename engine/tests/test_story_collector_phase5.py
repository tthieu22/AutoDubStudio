import json
import shutil
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch, MagicMock

from autodub.models.project import Project
from autodub.modules.story_collector import StoryCollector, GutenbergCollector, WikisourceCollector

class TestPhase5StoryCollector(unittest.TestCase):
    def setUp(self):
        self.test_dir = Path(tempfile.mkdtemp(prefix="autodub_p5_test_"))
        self.project_dir = self.test_dir / "story_proj_001"
        self.project = Project(self.project_dir, name="story_test", mode="MODE_STORY")

    def tearDown(self):
        if self.test_dir.exists():
            shutil.rmtree(self.test_dir, ignore_errors=True)

    @patch("requests.get")
    def test_01_gutenberg_collector_search(self, mock_get):
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "results": [
                {
                    "id": 1234,
                    "title": "Dracula",
                    "authors": [{"name": "Stoker, Bram"}],
                    "formats": {"text/plain; charset=utf-8": "https://www.gutenberg.org/files/1234/1234-0.txt"}
                }
            ]
        }
        mock_get.return_value = mock_response

        books = GutenbergCollector.search_books(topic="vampire", language="en", limit=1)
        self.assertEqual(len(books), 1)
        self.assertEqual(books[0]["title"], "Dracula")
        self.assertEqual(books[0]["license"], "public_domain")

    @patch("requests.get")
    def test_02_wikisource_collector_fetch(self, mock_get):
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "query": {
                "pages": {
                    "999": {
                        "title": "Liêu Trai Chí Dị",
                        "revisions": [{"*": "== Chương 1 ==\nNgày xửa ngày xưa..."}]
                    }
                }
            }
        }
        mock_get.return_value = mock_response

        data = WikisourceCollector.fetch_page("Liêu Trai Chí Dị", language="vi")
        self.assertEqual(data["title"], "Liêu Trai Chí Dị")
        self.assertEqual(data["license"], "public_domain")
        self.assertIn("Ngày xửa ngày xưa", data["raw_content"])

    @patch("requests.get")
    def test_03_story_collector_integration(self, mock_get):
        # Mock text response
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.text = "*** START OF THE PROJECT GUTENBERG EBOOK ***\nOnce upon a time in a dark forest..."
        mock_get.return_value = mock_response

        collector = StoryCollector(self.project)
        meta = collector.collect("gutenberg", "https://www.gutenberg.org/files/1234/1234-0.txt", language="en")

        self.assertEqual(meta["status"], "FETCHED")
        self.assertTrue((self.project_dir / "story" / "original.txt").exists())
        self.assertTrue((self.project_dir / "source" / "story_source.json").exists())

        txt_content = (self.project_dir / "story" / "original.txt").read_text(encoding="utf-8")
        self.assertIn("Once upon a time", txt_content)

if __name__ == "__main__":
    unittest.main()
