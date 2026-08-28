import os
import tempfile
import unittest
from pathlib import Path
from autodub.novel.novel_models import StoryIdea, CanonFact
from autodub.novel.novel_database import NovelDatabase
from autodub.novel.context_builder import ContextBuilder
from autodub.novel.canon_validator_engine import CanonValidatorEngine
from autodub.novel.novel_engine import NovelEngine


class MockLlamaClient:
    def generate(self, prompt: str, timeout: int = 120) -> str:
        if "STORY DIRECTOR" in prompt:
            return '{"premise": "Test premise", "cultivation_system": [{"rank":1, "name":"Luyện Khí"}], "characters": [{"id":"char_001", "name":"Lâm Phàm", "realm":"Luyện Khí"}]}'
        elif "MASTER PLANNER" in prompt:
            return '[{"arc_num": 1, "title": "Arc 1", "start_chapter": 1, "end_chapter": 50, "goal": "Goal 1"}]'
        elif "CHAPTER PLANNER" in prompt:
            return '{"chapter_num": 1, "goal": "Đột phá Trúc Cơ", "conflict": "Yêu thú cản đường", "characters": ["char_001"]}'
        elif "CREATIVE ENGINE" in prompt:
            return '{"option_a": {"title": "A", "description": "Desc"}}'
        elif "SCENE PLANNER" in prompt:
            return '[{"scene_index": 1, "goal": "Gặp yêu thú", "emotion": "Căng thẳng", "conflict": "Chiến đấu", "ending": "Đánh thắng"}]'
        elif "NOVEL WRITER" in prompt:
            return 'Lâm Phàm đối mặt với yêu thú trong hang động linh khí...'
        elif "NOVEL EDITOR" in prompt:
            return '{"edited_text": "Lâm Phàm đi vào hang động linh khí đậm đặc và đối mặt với yêu thú dữ tợn."}'
        elif "MEMORY EXTRACTOR" in prompt:
            return '{"summary": "Lâm Phàm chiến đấu yêu thú", "canon_facts": [{"category": "event", "fact_text": "Lâm Phàm đánh bại yêu thú hang động"}]}'
        return '{}'


class TestNovelEnginePipeline(unittest.TestCase):
    def test_full_engine_pipeline(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            story_dir = Path(tmp_dir) / "test_novel_001"
            mock_llm = MockLlamaClient()
            engine = NovelEngine(story_dir=story_dir, story_id="story_test", llm_client=mock_llm)

            # 1. Test Initialize Story
            idea = StoryIdea(title="Độc Cô Cầu Bại", total_chapters=100)
            bible = engine.initialize_story(idea)
            self.assertIsNotNone(bible)
            self.assertEqual(bible.premise, "Test premise")

            # 2. Test Master Planner
            arcs = engine.generate_master_plan(100)
            self.assertEqual(len(arcs), 1)
            self.assertEqual(arcs[0].title, "Arc 1")

            # 3. Test Generate Chapter 1
            chap_res = engine.generate_chapter(1)
            self.assertEqual(chap_res["chapter_num"], 1)
            self.assertIn("Lâm Phàm", chap_res["text"])
            self.assertTrue(os.path.exists(chap_res["file"]))

            # 4. Verify DB was populated
            facts = engine.db.get_canon_facts("story_test", limit=10)
            self.assertEqual(len(facts), 1)
            self.assertIn("yêu thú", facts[0]["fact_text"])


if __name__ == "__main__":
    unittest.main()
