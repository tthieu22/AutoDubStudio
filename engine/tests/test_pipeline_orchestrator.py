import unittest
import tempfile
from pathlib import Path
from unittest.mock import MagicMock

from autodub.novel.novel_database import NovelDatabase
from autodub.novel.novel_models import StoryIdea, GenerationError
from autodub.novel.pipeline_orchestrator import PipelineOrchestrator


class TestPipelineOrchestrator(unittest.TestCase):

    def setUp(self):
        self.tmp_dir = tempfile.TemporaryDirectory()
        self.db_path = Path(self.tmp_dir.name) / "test_story.db"
        self.db = NovelDatabase(self.db_path)
        self.story_id = "story_test_001"

        idea = StoryIdea(
            title="Đại Lục Chi Vương",
            genre="Sci-Fi",
            protagonist={"name": "Diệp Phàm", "background": "Kỹ Sư Vũ Trụ"}
        )
        self.db.create_story(self.story_id, idea)

        self.mock_llm = MagicMock()
        self.mock_llm.generate.return_value = '{"status": "PASS"}'
        self.mock_llm.extract_json.side_effect = lambda text: {
            "character_updates": [{"character_id": "char_001", "status_change": "Trở thành cơ trưởng", "evidence": {"chapter": 1, "source": "narration", "text_reference": "nhận chức cơ trưởng"}}],
            "world_updates": {"new_locations": [{"name": "Trạm Vũ Trụ Alpha", "description": "Trạm dừng chân"}]},
            "memory_updates": [{"character_id": "char_001", "fact_text": "Phát hiện tàu lạ", "information_state": "CONFIRMED", "evidence": {"chapter": 1}}],
            "level_updates": [{"character_id": "char_001", "previous_realm": "Rank D", "new_realm": "Rank C", "rank_number": 2, "breakthrough_type": "advance", "evidence": {"chapter": 1}}],
            "terminology_updates": [{"term_key": "Động Cơ Siêu Tốc", "canonical_name": "Động Cơ Siêu Tốc", "category": "Item", "definition": "Thiết bị nhảy vọt", "evidence": {"chapter": 1}}],
            "event_updates": [{"event_id": "evt_001", "title": "Cảnh Báo Đỏ", "status": "FACT", "evidence": {"chapter": 1}}],
            "relationship_updates": [{"source_entity": "char_001", "target_entity": "char_002", "relationship_type": "ALLIANCE", "status": "ESTABLISHED", "evidence": {"chapter": 1}}],
            "open_thread_updates": [{"thread_id": "thr_001", "title": "Bí Ẩn Tín Hiệu", "status": "NEW", "description": "Tín hiệu lạ", "evidence": {"chapter": 1}}],
            "status": "PASS",
            "failures": []
        }

    def tearDown(self):
        self.tmp_dir.cleanup()

    def test_pipeline_execution_pass_and_atomic_commit(self):
        orchestrator = PipelineOrchestrator(self.db, self.mock_llm)
        res = orchestrator.process_chapter_pipeline(
            story_id=self.story_id,
            chapter_num=1,
            chapter_text="Diệp Phàm bước vào Trạm Vũ Trụ Alpha và nhận chức cơ trưởng.",
            story_bible={"world": {"continent_name": "Vũ Trụ Vô Tận"}}
        )

        self.assertEqual(res["status"], "PASS")
        self.assertIn("character", res["domain_results"])
        self.assertIn("world", res["domain_results"])

        # Verify DB updates committed atomically
        facts = self.db.get_confirmed_facts(self.story_id)
        self.assertTrue(any("Trạm Vũ Trụ Alpha" in f.get("fact_text", "") for f in facts))

    def test_pipeline_fail_closed_on_validator_failure(self):
        # Mock validator to fail
        failing_llm = MagicMock()
        failing_llm.generate.return_value = '{"status": "FAIL"}'
        failing_llm.extract_json.side_effect = lambda text: {
            "status": "FAIL",
            "failures": [{"domain": "Memory", "entity": "char_001", "field_name": "information_state", "problem": "Knowledge Leak", "evidence": "text", "severity": "CRITICAL"}]
        }

        orchestrator = PipelineOrchestrator(self.db, failing_llm)
        with self.assertRaises(GenerationError) as cm:
            orchestrator.process_chapter_pipeline(
                story_id=self.story_id,
                chapter_num=1,
                chapter_text="Thất bại thẩm định"
            )

        self.assertEqual(cm.exception.stage, "CANON_VALIDATOR")


if __name__ == "__main__":
    unittest.main()
