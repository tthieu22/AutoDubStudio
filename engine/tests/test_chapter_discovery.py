import unittest
from unittest.mock import patch, MagicMock
from pathlib import Path
import tempfile
import shutil

from autodub.discovery.link_discovery import LinkDiscovery
from autodub.discovery.pagination_handler import PaginationHandler
from autodub.discovery.pattern_detector import PatternDetector
from autodub.discovery.generator import generate_chapter_urls
from autodub.discovery.validator import ChapterValidator
from autodub.discovery.registry import ChapterRegistry
from autodub.discovery.engine import AdaptiveDiscoveryEngine

HTML_SAMPLE_NETTRUYEN = """
<!DOCTYPE html>
<html>
<head><title>Bách Luyện Thành Thần - Nettruyen</title></head>
<body>
<div class="list-chapter">
    <a href="/truyen-tranh/bach-luyen-thanh-than/chuong-1294">Chương 1294: Quy Tắc Mới</a>
    <a href="/truyen-tranh/bach-luyen-thanh-than/chuong-1293">Chương 1293: Phong Ấn</a>
    <a href="/truyen-tranh/bach-luyen-thanh-than/chuong-1292">Chương 1292: Đại Chiến</a>
    <a href="/truyen-tranh/bach-luyen-thanh-than/chuong-1">Chương 1: Khởi Đầu</a>
</div>
<a href="/truyen-tranh/bach-luyen-thanh-than?page=2" class="load-more">Xem thêm</a>
</body>
</html>
"""

class TestAdaptiveChapterDiscovery(unittest.TestCase):
    def setUp(self):
        self.test_dir = Path(tempfile.mkdtemp(prefix="autodub_discovery_test_"))
        self.base_url = "https://nettruyen.gg/truyen-tranh/bach-luyen-thanh-than"

    def tearDown(self):
        if self.test_dir.exists():
            shutil.rmtree(self.test_dir, ignore_errors=True)

    def test_01_link_discovery(self):
        links = LinkDiscovery.extract_chapter_links(self.base_url, HTML_SAMPLE_NETTRUYEN)
        self.assertGreaterEqual(len(links), 4)
        ch_nums = [l["chapterNumber"] for l in links]
        self.assertIn(1, ch_nums)
        self.assertIn(1294, ch_nums)

    def test_02_pagination_detection(self):
        res = PaginationHandler.detect_pagination_and_api(self.base_url, HTML_SAMPLE_NETTRUYEN)
        self.assertTrue(res["hasLoadMore"])
        self.assertEqual(len(res["nextPageUrls"]), 1)
        self.assertIn("page=2", res["nextPageUrls"][0])

    def test_03_pattern_detection(self):
        links = LinkDiscovery.extract_chapter_links(self.base_url, HTML_SAMPLE_NETTRUYEN)
        pat = PatternDetector.detect_pattern(links)
        self.assertIsNotNone(pat)
        self.assertIn("{number}", pat["pattern"])
        self.assertEqual(pat["start"], 1)
        self.assertEqual(pat["end"], 1294)

    def test_04_deterministic_generator(self):
        pattern = "https://nettruyen.gg/truyen-tranh/bach-luyen-thanh-than/chuong-{number}"
        candidates = generate_chapter_urls(pattern, start=1, end=5, step=1)
        self.assertEqual(len(candidates), 5)
        self.assertEqual(candidates[0]["url"], "https://nettruyen.gg/truyen-tranh/bach-luyen-thanh-than/chuong-1")
        self.assertEqual(candidates[4]["url"], "https://nettruyen.gg/truyen-tranh/bach-luyen-thanh-than/chuong-5")

        # Unsupported pattern test
        with self.assertRaises(ValueError):
            generate_chapter_urls("https://invalid-url.com/no-placeholder")

    def test_05_registry_deduplication_and_bounds(self):
        registry_file = self.test_dir / "registry.json"
        reg = ChapterRegistry(self.base_url, registry_file=registry_file)
        reg.add_or_update_chapter(1, "Chương 1", "https://site.com/c1", discovered_by="HTML_LINK")
        reg.add_or_update_chapter(2, "Chương 2", "https://site.com/c2", discovered_by="HTML_LINK")
        reg.add_or_update_chapter(5, "Chương 5", "https://site.com/c5", discovered_by="PATTERN")

        self.assertEqual(reg.lowest_chapter, 1)
        self.assertEqual(reg.highest_chapter, 5)
        self.assertEqual(reg.missing_chapters, [3, 4])

        # Test duplicate adding
        reg.add_or_update_chapter(1, "Chương 1 (Alt)", "https://site.com/c1", discovered_by="PATTERN")
        self.assertEqual(len(reg.chapters), 3)

        reg.save()
        self.assertTrue(registry_file.exists())

    @patch("requests.get")
    def test_06_engine_end_to_end(self, mock_get):
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.text = HTML_SAMPLE_NETTRUYEN
        mock_response.history = []
        mock_get.return_value = mock_response

        engine = AdaptiveDiscoveryEngine(
            story_url=self.base_url,
            registry_file=self.test_dir / "test_registry.json"
        )
        res = engine.run()
        self.assertGreaterEqual(res["totalCandidates"], 4)
        self.assertIn("HTML_LINK", res["discoveryMethods"])

if __name__ == "__main__":
    unittest.main()
