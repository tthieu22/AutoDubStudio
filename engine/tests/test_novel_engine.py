import os
import json
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
        # Step 1A: World & Premise
        if "STORY DIRECTOR" in prompt and ("Bối Cảnh" in prompt or "Premise" in prompt or "Thế Giới Quan" in prompt):
            return '{"premise": "Test premise", "world": {"continent_name": "Test Continent", "locations": ["Loc 1"], "factions": ["Faction A"]}}'
        # Step 1B: Progression System
        elif "STORY DIRECTOR" in prompt and ("Cảnh Giới" in prompt or "Progression" in prompt or "Sức Mạnh" in prompt):
            return '{"progression_system": {"type": "cultivation", "ranks": [{"rank":1, "name":"Sơ Cấp"}, {"rank":2, "name":"Trung Cấp"}]}, "cultivation_system": [{"rank":1, "name":"Sơ Cấp"}, {"rank":2, "name":"Trung Cấp"}]}'
        # Step 1C: Cast Generation
        elif "STORY DIRECTOR" in prompt and ("Nhân Vật" in prompt or "Cast" in prompt):
            return '[{"id":"char_001", "name":"Lâm Phàm", "gender":"Nam", "personality":["Điềm tĩnh"], "goal":"Mạnh nhất", "realm":"Sơ Cấp", "location":"Loc 1", "known_information":["Bối cảnh"], "secrets":["Bí mật"]}, {"id":"char_002", "name":"Nguyệt Nhi", "gender":"Nữ", "personality":["Thông minh"], "goal":"Bảo vệ", "realm":"Sơ Cấp", "location":"Loc 1", "known_information":["Bối cảnh"], "secrets":[]}]'
        # Step 1D: World Rules
        elif "STORY DIRECTOR" in prompt and ("Quy Tắc" in prompt or "Rules" in prompt):
            return '["Cấp độ tuân thủ nghiêm ngặt", "Nhân vật không biết trước tương lai", "Không được phá quy tắc thế giới"]'
        # Step 1E: Terminology
        elif "STORY DIRECTOR" in prompt and ("Thuật Ngữ" in prompt or "Terminology" in prompt):
            return '{"linh khí": "Năng lượng tu luyện cơ bản", "đột phá": "Nâng cấp cảnh giới"}'
        # Fallback for any STORY DIRECTOR prompt
        elif "STORY DIRECTOR" in prompt:
            return '{"premise": "Test premise", "world": {"continent_name": "Test Continent", "locations": ["Loc 1"]}, "progression_system": {"type": "cultivation", "ranks": [{"rank":1, "name":"Sơ Cấp"}]}, "cultivation_system": [{"rank":1, "name":"Sơ Cấp"}], "characters": [{"id":"char_001", "name":"Lâm Phàm", "realm":"Sơ Cấp"}], "rules": ["Rule 1"], "terminology": {"linh khí": "Năng lượng"}}'
        # Step 1F: Master Story Blueprint
        elif "MASTER STORY BLUEPRINT ARCHITECT" in prompt:
            return '{"overall_arc_summary": "Tóm tắt kịch bản tổng thể test 1000 chương", "core_conflicts_and_mysteries": ["Mâu thuẫn 1"], "protagonist_growth_milestones": ["Cột mốc 1"], "major_climaxes_and_twists": ["Twist 1"], "world_timeline_events": ["Sự kiện 1"]}'
        elif "ARC ROADMAP ARCHITECT" in prompt:
            return '[{"chapter_num": 1, "title": "Chương 1: Xuất sơn", "goal": "Khám phá hang động", "trigger_event": "Phát hiện yêu thú", "conflict": "Giao chiến", "revelation": "Cổ thư", "transition_hook": "Rút lui"}]'
        elif "MASTER PLANNER" in prompt:
            return '[{"arc_num": 1, "title": "Arc 1", "start_chapter": 1, "end_chapter": 20, "goal": "Goal 1", "conflict": "Conflict 1", "major_reveal": "Reveal 1", "character_development": "Dev 1"}, {"arc_num": 2, "title": "Arc 2", "start_chapter": 21, "end_chapter": 40, "goal": "Goal 2", "conflict": "Conflict 2", "major_reveal": "Reveal 2", "character_development": "Dev 2"}]'
        elif "CHAPTER PLANNER" in prompt:
            return '{"chapter_num": 1, "goal": "Đột phá Trúc Cơ", "conflict": "Yêu thú cản đường", "characters": ["char_001"]}'
        elif "CREATIVE ENGINE" in prompt:
            return '{"option_a": {"title": "A", "description": "Desc"}}'
        elif "SCENE PLANNER" in prompt:
            return '[{"scene_index": 1, "goal": "Gặp yêu thú", "emotion": "Căng thẳng", "conflict": "Chiến đấu", "ending": "Đánh thắng"}]'
        elif "NOVEL WRITER" in prompt:
            return 'Lâm Phàm sải bước tiến vào hang động linh khí đậm đặc, đối mặt với con yêu thú dữ tợn và dùng kiếm trảm sát nó để giải mã bí mật cổ thư.'
        elif "NOVEL EDITOR" in prompt:
            return '{"edited_text": "Lâm Phàm sải bước tiến vào hang động linh khí đậm đặc, đối mặt với con yêu thú dữ tợn và dùng kiếm trảm sát nó để giải mã bí mật cổ thư."}'
        elif "MEMORY EXTRACTOR" in prompt:
            return '{"summary": "Lâm Phàm chiến đấu yêu thú", "canon_facts": [{"category": "event", "fact_text": "Lâm Phàm đánh bại yêu thú hang động"}]}'
        return '{}'


class TestNovelEnginePipeline(unittest.TestCase):
    def test_full_engine_pipeline(self):
        with tempfile.TemporaryDirectory(ignore_cleanup_errors=True) as tmp_dir:
            story_dir = Path(tmp_dir) / "test_novel_001"
            mock_llm = MockLlamaClient()
            engine = NovelEngine(story_dir=story_dir, story_id="story_test", llm_client=mock_llm)

            # 1. Test Initialize Story (World Bible)
            idea = StoryIdea(title="Độc Cô Cầu Bại", total_chapters=100)
            bible = engine.initialize_story(idea)
            self.assertIsNotNone(bible)
            self.assertEqual(bible.premise, "Test premise")

            # 2. Test Master Planner & Master Blueprint Skeleton (Prompt 1F generated AFTER Arcs)
            arcs = engine.generate_master_plan(100)
            self.assertGreaterEqual(len(arcs), 5)
            self.assertEqual(arcs[0].title, "Arc 1")

            bible_path = story_dir / "story_bible.json"
            self.assertTrue(bible_path.exists())
            with open(bible_path, "r", encoding="utf-8") as f:
                updated_bible = json.load(f)
            self.assertIsNotNone(updated_bible.get("master_blueprint"))




            # 2b. Test Arc Roadmap Generation
            roadmap = engine.story_planner.generate_arc_roadmap(1)
            self.assertIsInstance(roadmap, list)
            self.assertGreater(len(roadmap), 0)

            # 3. Test Generate Chapter 1
            chap_res = engine.generate_chapter(1)
            self.assertEqual(chap_res["chapter_num"], 1)
            self.assertIn("Lâm Phàm", chap_res["text"])
            self.assertTrue(os.path.exists(chap_res["file"]))


            # 4. Verify DB was populated
            facts = engine.db.get_canon_facts("story_test", limit=10)
            self.assertEqual(len(facts), 1)
            self.assertIn("yêu thú", facts[0]["fact_text"])

            engine.db.close()


if __name__ == "__main__":
    unittest.main()
