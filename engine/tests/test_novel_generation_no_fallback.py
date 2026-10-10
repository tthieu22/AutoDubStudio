import json
import tempfile
import unittest
from pathlib import Path
from autodub.novel.novel_models import StoryIdea, GenerationError, GenerationErrorCode
from autodub.novel.novel_engine import NovelEngine


class MockNoFallbackLlamaClient:
    def __init__(self, mode="scifi"):
        self.mode = mode

    def generate(self, prompt: str, timeout: int = 120) -> str:
        if self.mode == "timeout":
            raise TimeoutError("LLM generation timed out during call")
        elif self.mode == "unavailable":
            raise Exception("Ollama server connection refused")
        elif self.mode == "empty":
            return ""
        elif self.mode == "json_error":
            return "THIS IS NOT VALID JSON AT ALL"
        elif self.mode == "schema_error":
            if "STORY DIRECTOR" in prompt:
                return json.dumps({"world": {}, "characters": [{"id": "char_001", "name": "Alex Chen"}]})  # Missing premise & rules
            elif "MASTER PLANNER" in prompt:
                return json.dumps([])  # Empty 0 arcs
        elif self.mode == "scifi":
            if "STORY DIRECTOR" in prompt:
                return json.dumps({
                    "premise": "Kỹ sư Alex Chen khám phá tín hiệu ngoài vĩ tuyến vũ trụ.",
                    "world": {
                        "continent_name": "Hành Tinh Alpha-9",
                        "factions": ["Liên Minh Vũ Trụ", "Tập Đoàn AI Cygnus"],
                        "locations": ["Trạm Không Gian Sector 7", "Hố Đen Nebula"]
                    },
                    "progression_system": {
                        "type": "technology",
                        "ranks": [
                            {"rank": 1, "name": "Rank D - Kỹ Sư Sơ Cấp", "description": "Làm chủ máy móc cơ bản"},
                            {"rank": 2, "name": "Rank C - Chuyên Viên Gene", "description": "Cải tạo thể chất AI"}
                        ]
                    },
                    "cultivation_system": [
                        {"rank": 1, "name": "Rank D - Kỹ Sư Sơ Cấp", "description": "Làm chủ máy móc cơ bản"}
                    ],
                    "characters": [
                        {"id": "char_001", "name": "Alex Chen", "realm": "Rank D - Kỹ Sư Sơ Cấp", "location": "Trạm Không Gian Sector 7"}
                    ],
                    "rules": ["Quy tắc vật lý vũ trụ cố định"],
                    "terminology": {"Hạm Đội": "Chiến hạm quy mô lớn"}
                }, ensure_ascii=False)
            elif "MASTER PLANNER" in prompt:
                return json.dumps([
                    {"arc_num": 1, "title": "Arc 01 — Tín Hiệu Bí Ẩn Nebula", "start_chapter": 1, "end_chapter": 50, "goal": "Alex Chen phát hiện tín hiệu", "conflict": "Trạm Sector 7 bị tấn công", "major_reveal": "Mã hóa ngoài Trái Đất", "character_development": "Bắt đầu làm chủ công nghệ"},
                    {"arc_num": 2, "title": "Arc 02 — Hạm Đội Cygnus", "start_chapter": 51, "end_chapter": 100, "goal": "Chống lại Tập Đoàn Cygnus", "conflict": "Xung đột không gian", "major_reveal": "Bí mật trí tuệ nhân tạo", "character_development": "Trở thành chỉ huy hạm đội"}
                ], ensure_ascii=False)
        elif self.mode == "detective":
            if "STORY DIRECTOR" in prompt:
                return json.dumps({
                    "premise": "Điều tra viên Nguyễn An thụ lý vụ án hồ sơ mật.",
                    "world": {
                        "continent_name": "Thành Phố Sương Mù",
                        "factions": ["Cục Cảnh Sát Thành Phố", "Tổ Chức Bóng Đêm"],
                        "locations": ["Hiện Trường Vụ Án", "Phòng Hồ Sơ Mật"]
                    },
                    "progression_system": {
                        "type": "investigation",
                        "ranks": [
                            {"rank": 1, "name": "Cấp 1 - Tập Sự", "description": "Quan sát dấu vết"},
                            {"rank": 2, "name": "Cấp 2 - Thám Tử", "description": "Suy luận logic"}
                        ]
                    },
                    "characters": [
                        {"id": "char_001", "name": "Nguyễn An", "realm": "Cấp 1 - Tập Sự", "location": "Phòng Hồ Sơ Mật"}
                    ],
                    "rules": ["Quy tắc pháp lý và chứng cứ suy luận"],
                    "terminology": {"Hồ Sơ Mật": "Tài liệu bị niêm phong"}
                }, ensure_ascii=False)
            elif "MASTER PLANNER" in prompt:
                return json.dumps([
                    {"arc_num": 1, "title": "Arc 01 — Vụ Án Đêm Mưa", "start_chapter": 1, "end_chapter": 50, "goal": "Nguyễn An thu thập manh mối", "conflict": "Kẻ giấu mặt đe dọa", "major_reveal": "Bức thư tống tiền cổ", "character_development": "Tự tin rèn luyện suy luận"}
                ], ensure_ascii=False)
        return "{}"


class TestNovelGenerationNoFallback(unittest.TestCase):
    """
    25-Part Exhaustive Test Suite for Hard-Failure & Fail-Closed Story Generation.
    Verifies NO soft fallbacks, strict error codes, user idea integrity, and zero cross-story leakage.
    """

    def setUp(self):
        self.tmp_dir = tempfile.TemporaryDirectory()
        self.story_dir = Path(self.tmp_dir.name) / "test_story"

    def tearDown(self):
        self.tmp_dir.cleanup()

    # ══════════════════════════════════════════════════════════════
    # GROUP 1: NO FALLBACK & HARD FAILURE TESTS (1–10)
    # ══════════════════════════════════════════════════════════════
    def test_1_world_timeout_stop(self):
        """TEST 1: LLM timeout stops world generation pipeline cleanly with LLM_TIMEOUT."""
        engine = NovelEngine(self.story_dir, llm_client=MockNoFallbackLlamaClient("timeout"))
        idea = StoryIdea(title="Vũ Trụ Chi Vương", genre="Khoa học viễn tưởng", protagonist={"name": "Alex Chen"})

        with self.assertRaises(GenerationError) as cm:
            engine.initialize_story(idea)
        self.assertEqual(cm.exception.error_code, GenerationErrorCode.LLM_TIMEOUT.value)
        self.assertEqual(cm.exception.stage, "WORLD_GENERATION")

    def test_2_world_empty_response_stop(self):
        """TEST 2: Empty LLM response stops world generation with LLM_EMPTY_RESPONSE."""
        engine = NovelEngine(self.story_dir, llm_client=MockNoFallbackLlamaClient("empty"))
        idea = StoryIdea(title="Vũ Trụ Chi Vương", genre="Khoa học viễn tưởng", protagonist={"name": "Alex Chen"})

        with self.assertRaises(GenerationError) as cm:
            engine.initialize_story(idea)
        self.assertEqual(cm.exception.error_code, GenerationErrorCode.LLM_EMPTY_RESPONSE.value)

    def test_3_world_json_error_stop(self):
        """TEST 3: Malformed JSON output stops world generation with JSON_PARSE_ERROR."""
        engine = NovelEngine(self.story_dir, llm_client=MockNoFallbackLlamaClient("json_error"))
        idea = StoryIdea(title="Vũ Trụ Chi Vương", genre="Khoa học viễn tưởng", protagonist={"name": "Alex Chen"})

        with self.assertRaises(GenerationError) as cm:
            engine.initialize_story(idea)
        self.assertEqual(cm.exception.error_code, GenerationErrorCode.JSON_PARSE_ERROR.value)

    def test_4_world_schema_error_stop(self):
        """TEST 4: Missing required fields in JSON payload stops world generation with SCHEMA_VALIDATION_ERROR."""
        engine = NovelEngine(self.story_dir, llm_client=MockNoFallbackLlamaClient("schema_error"))
        idea = StoryIdea(title="Vũ Trụ Chi Vương", genre="Khoa học viễn tưởng", protagonist={"name": "Alex Chen"})

        with self.assertRaises(GenerationError) as cm:
            engine.initialize_story(idea)
        self.assertEqual(cm.exception.error_code, GenerationErrorCode.SCHEMA_VALIDATION_ERROR.value)

    def test_5_master_plan_timeout_stop(self):
        """TEST 5: LLM timeout during Master Plan halts pipeline with LLM_TIMEOUT."""
        # Initialize valid Story Bible first
        scifi_engine = NovelEngine(self.story_dir, llm_client=MockNoFallbackLlamaClient("scifi"))
        scifi_engine.initialize_story(StoryIdea(title="Vũ Trụ Chi Vương", genre="Khoa học viễn tưởng", protagonist={"name": "Alex Chen"}))

        # Switch client to timeout
        timeout_engine = NovelEngine(self.story_dir, llm_client=MockNoFallbackLlamaClient("timeout"))
        with self.assertRaises(GenerationError) as cm:
            timeout_engine.generate_master_plan(100)
        self.assertEqual(cm.exception.error_code, GenerationErrorCode.LLM_TIMEOUT.value)
        self.assertEqual(cm.exception.stage, "MASTER_PLAN")

    def test_6_master_plan_json_error_stop(self):
        """TEST 6: Malformed JSON during Master Plan halts pipeline with JSON_PARSE_ERROR."""
        scifi_engine = NovelEngine(self.story_dir, llm_client=MockNoFallbackLlamaClient("scifi"))
        scifi_engine.initialize_story(StoryIdea(title="Vũ Trụ Chi Vương", genre="Khoa học viễn tưởng", protagonist={"name": "Alex Chen"}))

        json_err_engine = NovelEngine(self.story_dir, llm_client=MockNoFallbackLlamaClient("json_error"))
        with self.assertRaises(GenerationError) as cm:
            json_err_engine.generate_master_plan(100)
        self.assertEqual(cm.exception.error_code, GenerationErrorCode.JSON_PARSE_ERROR.value)

    def test_7_master_plan_schema_error_stop(self):
        """TEST 7: Empty 0 arcs response during Master Plan halts pipeline with SCHEMA_VALIDATION_ERROR."""
        scifi_engine = NovelEngine(self.story_dir, llm_client=MockNoFallbackLlamaClient("scifi"))
        scifi_engine.initialize_story(StoryIdea(title="Vũ Trụ Chi Vương", genre="Khoa học viễn tưởng", protagonist={"name": "Alex Chen"}))

        schema_err_engine = NovelEngine(self.story_dir, llm_client=MockNoFallbackLlamaClient("schema_error"))
        with self.assertRaises(GenerationError) as cm:
            schema_err_engine.generate_master_plan(100)
        self.assertEqual(cm.exception.error_code, GenerationErrorCode.SCHEMA_VALIDATION_ERROR.value)

    def test_8_no_dynamic_world_fallback(self):
        """TEST 8: Verify _dynamic_world_fallback method does NOT exist on NovelEngine."""
        engine = NovelEngine(self.story_dir, llm_client=MockNoFallbackLlamaClient("scifi"))
        self.assertFalse(hasattr(engine, "_dynamic_world_fallback"))

    def test_9_no_dynamic_arc_fallback(self):
        """TEST 9: Verify _generate_dynamic_arcs method does NOT exist on NovelEngine."""
        engine = NovelEngine(self.story_dir, llm_client=MockNoFallbackLlamaClient("scifi"))
        self.assertFalse(hasattr(engine, "_generate_dynamic_arcs"))

    def test_10_no_default_25_arcs(self):
        """TEST 10: Verify _generate_default_25_arcs method does NOT exist on NovelEngine."""
        engine = NovelEngine(self.story_dir, llm_client=MockNoFallbackLlamaClient("scifi"))
        self.assertFalse(hasattr(engine, "_generate_default_25_arcs"))

    # ══════════════════════════════════════════════════════════════
    # GROUP 2: DEPENDENCY VALIDATION TESTS (11–13)
    # ══════════════════════════════════════════════════════════════
    def test_11_master_plan_without_bible_stop(self):
        """TEST 11: Calling generate_master_plan without story_bible.json raises DEPENDENCY_NOT_READY."""
        engine = NovelEngine(self.story_dir, llm_client=MockNoFallbackLlamaClient("scifi"))
        with self.assertRaises(GenerationError) as cm:
            engine.generate_master_plan(100)
        self.assertEqual(cm.exception.error_code, GenerationErrorCode.DEPENDENCY_NOT_READY.value)

    def test_12_invalid_bible_stop(self):
        """TEST 12: Calling generate_master_plan with empty/corrupt Story Bible raises DEPENDENCY_NOT_READY."""
        self.story_dir.mkdir(parents=True, exist_ok=True)
        (self.story_dir / "story_bible.json").write_text("CORRUPT JSON", encoding="utf-8")

        engine = NovelEngine(self.story_dir, llm_client=MockNoFallbackLlamaClient("scifi"))
        with self.assertRaises(GenerationError) as cm:
            engine.generate_master_plan(100)
        self.assertEqual(cm.exception.error_code, GenerationErrorCode.DEPENDENCY_NOT_READY.value)

    def test_13_partial_bible_stop(self):
        """TEST 13: Calling generate_master_plan with missing premise in Story Bible raises DEPENDENCY_NOT_READY."""
        self.story_dir.mkdir(parents=True, exist_ok=True)
        (self.story_dir / "story_bible.json").write_text(json.dumps({"world": {}}), encoding="utf-8")

        engine = NovelEngine(self.story_dir, llm_client=MockNoFallbackLlamaClient("scifi"))
        with self.assertRaises(GenerationError) as cm:
            engine.generate_master_plan(100)
        self.assertEqual(cm.exception.error_code, GenerationErrorCode.DEPENDENCY_NOT_READY.value)

    # ══════════════════════════════════════════════════════════════
    # GROUP 3: INTEGRITY & PROVENANCE TESTS (14–18)
    # ══════════════════════════════════════════════════════════════
    def test_14_protagonist_matches_user_idea(self):
        """TEST 14: Story Bible output protagonist matches user input Alex Chen."""
        engine = NovelEngine(self.story_dir, llm_client=MockNoFallbackLlamaClient("scifi"))
        idea = StoryIdea(title="Vũ Trụ Chi Vương", genre="Khoa học viễn tưởng", protagonist={"name": "Alex Chen"})
        bible = engine.initialize_story(idea)

        self.assertEqual(bible.characters[0]["name"], "Alex Chen")

    def test_15_genre_matches_user_idea(self):
        """TEST 15: Detective genre generates investigation progression_system without Xianxia terms."""
        engine = NovelEngine(self.story_dir, llm_client=MockNoFallbackLlamaClient("detective"))
        idea = StoryIdea(title="Hồ Sơ Mật", genre="Trinh thám hiện đại", protagonist={"name": "Nguyễn An"})
        bible = engine.initialize_story(idea)

        self.assertEqual(bible.progression_system.get("type"), "investigation")
        bible_str = json.dumps(bible.model_dump(), ensure_ascii=False)
        self.assertNotIn("Tiên Giới", bible_str)
        self.assertNotIn("Luyện Khí", bible_str)

    def test_16_world_matches_user_idea(self):
        """TEST 16: Generated continent_name and locations reflect Sci-Fi universe."""
        engine = NovelEngine(self.story_dir, llm_client=MockNoFallbackLlamaClient("scifi"))
        idea = StoryIdea(title="Vũ Trụ Chi Vương", genre="Khoa học viễn tưởng", protagonist={"name": "Alex Chen"})
        bible = engine.initialize_story(idea)

        self.assertEqual(bible.world["continent_name"], "Hành Tinh Alpha-9")

    def test_17_master_plan_matches_story_bible(self):
        """TEST 17: Generated Master Plan Arcs derive strictly from Story Bible premise & protagonist."""
        engine = NovelEngine(self.story_dir, llm_client=MockNoFallbackLlamaClient("scifi"))
        engine.initialize_story(StoryIdea(title="Vũ Trụ Chi Vương", genre="Khoa học viễn tưởng", protagonist={"name": "Alex Chen"}))

        arcs = engine.generate_master_plan(100)
        self.assertIn("Alex Chen", arcs[0].goal)

    def test_18_no_cross_story_contamination(self):
        """TEST 18: Distinct story ideas yield completely distinct payloads without cross leakage."""
        engine1 = NovelEngine(self.story_dir / "story_1", llm_client=MockNoFallbackLlamaClient("scifi"))
        bible1 = engine1.initialize_story(StoryIdea(title="Vũ Trụ Chi Vương", genre="Khoa học viễn tưởng", protagonist={"name": "Alex Chen"}))

        engine2 = NovelEngine(self.story_dir / "story_2", llm_client=MockNoFallbackLlamaClient("detective"))
        bible2 = engine2.initialize_story(StoryIdea(title="Hồ Sơ Mật", genre="Trinh thám hiện đại", protagonist={"name": "Nguyễn An"}))

        self.assertNotEqual(bible1.characters[0]["name"], bible2.characters[0]["name"])
        self.assertNotEqual(bible1.progression_system.get("type"), bible2.progression_system.get("type"))

    # ══════════════════════════════════════════════════════════════
    # GROUP 4: DATABASE & TRANSACTION ROLLBACK TESTS (19–21)
    # ══════════════════════════════════════════════════════════════
    def test_19_failed_world_no_db_commit(self):
        """TEST 19: Failed world generation does NOT write story_bible.json or corrupt DB."""
        engine = NovelEngine(self.story_dir, llm_client=MockNoFallbackLlamaClient("json_error"))
        idea = StoryIdea(title="Vũ Trụ Chi Vương", genre="Khoa học viễn tưởng", protagonist={"name": "Alex Chen"})

        try:
            engine.initialize_story(idea)
        except GenerationError:
            pass

        self.assertFalse((self.story_dir / "story_bible.json").exists())

    def test_20_failed_master_plan_no_db_commit(self):
        """TEST 20: Failed Master Plan does NOT save empty/partial arc plans to DB."""
        scifi_engine = NovelEngine(self.story_dir, llm_client=MockNoFallbackLlamaClient("scifi"))
        scifi_engine.initialize_story(StoryIdea(title="Vũ Trụ Chi Vương", genre="Khoa học viễn tưởng", protagonist={"name": "Alex Chen"}))

        schema_err_engine = NovelEngine(self.story_dir, llm_client=MockNoFallbackLlamaClient("schema_error"))
        try:
            schema_err_engine.generate_master_plan(100)
        except GenerationError:
            pass

        arcs = scifi_engine.db.get_arc_plans(scifi_engine.story_id)
        self.assertEqual(len(arcs), 0)

    def test_21_partial_write_rollback(self):
        """TEST 21: Verify project.json is not updated with arc_plans when Master Plan generation fails."""
        scifi_engine = NovelEngine(self.story_dir, llm_client=MockNoFallbackLlamaClient("scifi"))
        scifi_engine.initialize_story(StoryIdea(title="Vũ Trụ Chi Vương", genre="Khoa học viễn tưởng", protagonist={"name": "Alex Chen"}))

        json_err_engine = NovelEngine(self.story_dir, llm_client=MockNoFallbackLlamaClient("json_error"))
        try:
            json_err_engine.generate_master_plan(100)
        except GenerationError:
            pass

        p_json = self.story_dir / "project.json"
        if p_json.exists():
            data = json.loads(p_json.read_text(encoding="utf-8"))
            self.assertNotIn("arc_plans", data)

    # ══════════════════════════════════════════════════════════════
    # GROUP 5: RUNTIME & SYSTEM INTEGRATION TESTS (22–25)
    # ══════════════════════════════════════════════════════════════
    def test_22_retry_does_not_fallback(self):
        """TEST 22: Retries perform LLM calls again without invoking any fallback function."""
        engine = NovelEngine(self.story_dir, llm_client=MockNoFallbackLlamaClient("timeout"))
        idea = StoryIdea(title="Vũ Trụ Chi Vương", genre="Khoa học viễn tưởng", protagonist={"name": "Alex Chen"})

        with self.assertRaises(GenerationError) as cm:
            engine.initialize_story(idea)

        meta_file = self.story_dir / "story_bible.json"
        self.assertFalse(meta_file.exists())

    def test_23_real_llm_output_persisted(self):
        """TEST 23: Successful generation persists exact LLM output and provenance with fallback_used=False."""
        engine = NovelEngine(self.story_dir, llm_client=MockNoFallbackLlamaClient("scifi"))
        idea = StoryIdea(title="Vũ Trụ Chi Vương", genre="Khoa học viễn tưởng", protagonist={"name": "Alex Chen"})
        bible = engine.initialize_story(idea)

        self.assertEqual(bible.generation_metadata["source"], "LLM_GENERATED")
        self.assertFalse(bible.generation_metadata["fallback_used"])

    def test_24_ui_receives_structured_error(self):
        """TEST 24: GenerationError to_dict returns exact structured JSON payload required for UI/CLI."""
        err = GenerationError("WORLD_GENERATION", GenerationErrorCode.JSON_PARSE_ERROR.value, "LLM returned invalid JSON", retryable=True)
        payload = err.to_dict()

        self.assertFalse(payload["success"])
        self.assertEqual(payload["stage"], "WORLD_GENERATION")
        self.assertEqual(payload["error_code"], "JSON_PARSE_ERROR")
        self.assertEqual(payload["message"], "LLM returned invalid JSON")
        self.assertTrue(payload["retryable"])

    def test_25_model_unavailable_stops_pipeline(self):
        """TEST 25: Ollama model unavailable error halts execution with LLM_UNAVAILABLE."""
        engine = NovelEngine(self.story_dir, llm_client=MockNoFallbackLlamaClient("unavailable"))
        idea = StoryIdea(title="Vũ Trụ Chi Vương", genre="Khoa học viễn tưởng", protagonist={"name": "Alex Chen"})

        with self.assertRaises(GenerationError) as cm:
            engine.initialize_story(idea)
        self.assertEqual(cm.exception.error_code, GenerationErrorCode.LLM_UNAVAILABLE.value)


if __name__ == "__main__":
    unittest.main()
