import unittest
from unittest.mock import MagicMock
from autodub.novel.schemas import (
    CharacterDelta,
    WorldDelta,
    MemoryDelta,
    LevelDelta,
    TerminologyDelta,
    EventDelta,
    RelationshipDelta,
    OpenThreadDelta,
    ValidationReportPayload
)
from autodub.novel.engines import (
    CharacterEngine,
    WorldEngine,
    MemoryEngine,
    LevelEngine,
    TerminologyEngine,
    EventEngine,
    RelationshipEngine,
    OpenThreadEngine
)


class TestSpecializedPromptEngines(unittest.TestCase):

    def setUp(self):
        self.mock_llm = MagicMock()
        self.mock_llm.generate.return_value = '{"character_updates": [{"character_id": "char_001", "status_change": "Thăng cấp thành công", "evidence": {"chapter": 1, "source": "narration", "text_reference": "Diệp Phàm đột phá"}}]}'
        self.mock_llm.extract_json.side_effect = lambda text: {
            "character_updates": [{"character_id": "char_001", "status_change": "Thăng cấp thành công", "evidence": {"chapter": 1, "source": "narration", "text_reference": "Diệp Phàm đột phá"}}],
            "world_updates": {"new_locations": [{"name": "Bắc Đẩu Tinh"}]},
            "memory_updates": [{"character_id": "char_001", "fact_text": "Biết tin đồn", "information_state": "CONFIRMED", "evidence": {"chapter": 1}}],
            "level_updates": [{"character_id": "char_001", "previous_realm": "Rank D", "new_realm": "Rank C", "rank_number": 2, "breakthrough_type": "advance", "evidence": {"chapter": 1}}],
            "terminology_updates": [{"term_key": "Hồng Mông Khí", "canonical_name": "Hồng Mông Khí", "category": "Term", "definition": "Khí nguyên thủy", "evidence": {"chapter": 1}}],
            "event_updates": [{"event_id": "evt_001", "title": "Bão Vũ Trụ", "status": "FACT", "evidence": {"chapter": 1}}],
            "relationship_updates": [{"source_entity": "char_001", "target_entity": "char_002", "relationship_type": "ALLIANCE", "status": "ESTABLISHED", "evidence": {"chapter": 1}}],
            "open_thread_updates": [{"thread_id": "thr_001", "title": "Bí ẩn tàu vũ trụ", "status": "NEW", "description": "Tàu bỏ hoang", "evidence": {"chapter": 1}}]
        }

    def test_01_character_engine(self):
        engine = CharacterEngine(self.mock_llm)
        delta, meta = engine.analyze_chapter(1, "Bản thảo chương 1", [{"id": "char_001", "name": "Diệp Phàm"}], [])
        self.assertIn("character_updates", delta)
        self.assertEqual(meta["domain"], "character")
        self.assertEqual(meta["status"], "PASS")

    def test_02_world_engine(self):
        engine = WorldEngine(self.mock_llm)
        delta, meta = engine.analyze_chapter(1, "Bản thảo chương 1", {"continent_name": "Đại lục"}, [])
        self.assertIn("world_updates", delta)
        self.assertEqual(meta["domain"], "world")

    def test_03_memory_engine_information_states(self):
        engine = MemoryEngine(self.mock_llm)
        delta, meta = engine.analyze_chapter(1, "Bản thảo chương 1", [], [])
        self.assertIn("memory_updates", delta)
        self.assertEqual(delta["memory_updates"][0]["information_state"], "CONFIRMED")

    def test_04_level_engine(self):
        engine = LevelEngine(self.mock_llm)
        delta, meta = engine.analyze_chapter(1, "Bản thảo chương 1", [], [])
        self.assertIn("level_updates", delta)
        self.assertEqual(delta["level_updates"][0]["new_realm"], "Rank C")

    def test_05_terminology_engine(self):
        engine = TerminologyEngine(self.mock_llm)
        delta, meta = engine.analyze_chapter(1, "Bản thảo chương 1", {}, [])
        self.assertIn("terminology_updates", delta)
        self.assertEqual(delta["terminology_updates"][0]["term_key"], "Hồng Mông Khí")

    def test_06_event_engine(self):
        engine = EventEngine(self.mock_llm)
        delta, meta = engine.analyze_chapter(1, "Bản thảo chương 1", [], [])
        self.assertIn("event_updates", delta)

    def test_07_relationship_engine(self):
        engine = RelationshipEngine(self.mock_llm)
        delta, meta = engine.analyze_chapter(1, "Bản thảo chương 1", [], [])
        self.assertIn("relationship_updates", delta)

    def test_08_open_thread_engine(self):
        engine = OpenThreadEngine(self.mock_llm)
        delta, meta = engine.analyze_chapter(1, "Bản thảo chương 1", [], [])
        self.assertIn("open_thread_updates", delta)


if __name__ == "__main__":
    unittest.main()
