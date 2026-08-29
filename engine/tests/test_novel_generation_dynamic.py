import json
import tempfile
import unittest
from pathlib import Path
from autodub.novel.novel_models import StoryIdea
from autodub.novel.novel_engine import NovelEngine


class MockDynamicLlamaClient:
    def __init__(self, mode="scifi"):
        self.mode = mode

    def generate(self, prompt: str, timeout: int = 120) -> str:
        if "STORY DIRECTOR" in prompt:
            if self.mode == "scifi":
                return json.dumps({
                    "premise": "Kỹ sư Alex Chen khám phá tín hiệu ngoài vĩ tuyến vũ trụ.",
                    "world": {
                        "continent_name": "Hành Tinh Alpha-9",
                        "factions": ["Liên Minh Vũ Trụ", "Tập Đoàn AI Cygnus"],
                        "locations": ["Trạm Không Gian Sector 7", "Hố Đen Nebula"]
                    },
                    "cultivation_system": [
                        {"rank": 1, "name": "Rank D - Kỹ Sư Sơ Cấp", "description": "Làm chủ máy móc cơ bản"},
                        {"rank": 2, "name": "Rank C - Chuyên Viên Gene", "description": "Cải tạo thể chất AI"},
                        {"rank": 3, "name": "Rank B - Chỉ Huy Hạm Đội", "description": "Điều khiển chiến hạm"}
                    ],
                    "characters": [
                        {"id": "char_001", "name": "Alex Chen", "realm": "Rank D - Kỹ Sư Sơ Cấp", "location": "Trạm Không Gian Sector 7"}
                    ],
                    "rules": ["Quy tắc vật lý vũ trụ cố định"],
                    "terminology": {"Hạm Đội": "Chiến hạm quy mô lớn"}
                }, ensure_ascii=False)
            elif self.mode == "detective":
                return json.dumps({
                    "premise": "Điều tra viên Nguyễn An thụ lý vụ án hồ sơ mật.",
                    "world": {
                        "continent_name": "Thành Phố Sương Mù",
                        "factions": ["Cục Cảnh Sát Thành Phố", "Tổ Chức Bóng Đêm"],
                        "locations": ["Hiện Trường Vụ Án", "Phòng Hồ Sơ Mật"]
                    },
                    "cultivation_system": [
                        {"rank": 1, "name": "Cấp 1 - Tập Sự", "description": "Quan sát dấu vết"},
                        {"rank": 2, "name": "Cấp 2 - Thám Tử", "description": "Suy luận logic"}
                    ],
                    "characters": [
                        {"id": "char_001", "name": "Nguyễn An", "realm": "Cấp 1 - Tập Sự", "location": "Phòng Hồ Sơ Mật"}
                    ],
                    "rules": ["Quy tắc pháp lý và chứng cứ suy luận"],
                    "terminology": {"Hồ Sơ Mật": "Tài liệu bị niêm phong"}
                }, ensure_ascii=False)
            elif self.mode == "post_apocalyptic":
                return json.dumps({
                    "premise": "Khang dẫn dắt nhóm sống sót xây dựng nơi trú ẩn.",
                    "world": {
                        "continent_name": "Vùng Đất Phế Tích",
                        "factions": ["Nhóm Trú Ẩn Khang", "Băng Cướp Hoang Mạc"],
                        "locations": ["Căn Cứ Trú Ẩn", "Khu Phế Tích Nguyên Tử"]
                    },
                    "cultivation_system": [
                        {"rank": 1, "name": "Cấp 1 - Người Sống Sót", "description": "Thu thập nhu yếu phẩm"},
                        {"rank": 2, "name": "Cấp 2 - Xây Dựng", "description": "Tái tạo căn cứ"}
                    ],
                    "characters": [
                        {"id": "char_001", "name": "Khang", "realm": "Cấp 1 - Người Sống Sót", "location": "Căn Cứ Trú Ẩn"}
                    ],
                    "rules": ["Tài nguyên khan hiếm và quy tắc sinh tồn"],
                    "terminology": {"Nhu Yếu Phẩm": "Thức ăn và nước uống sạch"}
                }, ensure_ascii=False)
            elif self.mode == "injected_xianxia":
                # Simulated bad LLM output trying to inject Xianxia into Sci-Fi
                return json.dumps({
                    "premise": "Alex Chen đi đến Tiên Giới gia nhập Thanh Vân Tông.",
                    "characters": [{"id": "char_001", "name": "Lâm Phàm", "realm": "Trúc Cơ"}]
                }, ensure_ascii=False)
        elif "MASTER PLANNER" in prompt:
            if self.mode == "scifi":
                return json.dumps([
                    {"arc_num": 1, "title": "Arc 01 — Tín Hiệu Bí Ẩn Nebula", "start_chapter": 1, "end_chapter": 50, "goal": "Alex Chen phát hiện tín hiệu", "conflict": "Trạm Sector 7 bị tấn công", "major_reveal": "Mã hóa ngoài Trái Đất", "character_development": "Bắt đầu làm chủ công nghệ"},
                    {"arc_num": 2, "title": "Arc 02 — Hạm Đội Cygnus", "start_chapter": 51, "end_chapter": 100, "goal": "Chống lại Tập Đoàn Cygnus", "conflict": "Xung đột không gian", "major_reveal": "Bí mật trí tuệ nhân tạo", "character_development": "Trở thành chỉ huy hạm đội"}
                ], ensure_ascii=False)
            elif self.mode == "detective":
                return json.dumps([
                    {"arc_num": 1, "title": "Arc 01 — Vụ Án Đêm Mưa", "start_chapter": 1, "end_chapter": 50, "goal": "Nguyễn An thu thập manh mối", "conflict": "Kẻ giấu mặt đe dọa", "major_reveal": "Bức thư tống tiền cổ", "character_development": "Tự tin rèn luyện suy luận"}
                ], ensure_ascii=False)
            elif self.mode == "post_apocalyptic":
                return json.dumps([
                    {"arc_num": 1, "title": "Arc 01 — Căn Cứ Trú Ẩn Khang", "start_chapter": 1, "end_chapter": 50, "goal": "Khang tìm kiếm nguồn nước sạch", "conflict": "Băng Cướp cướp phá", "major_reveal": "Bản đồ căn cứ ngầm", "character_development": "Trở thành thủ lĩnh quyết đoán"}
                ], ensure_ascii=False)
            elif self.mode == "failed":
                return "MALFORMED JSON STRING"
        return "{}"


class TestNovelGenerationDynamic(unittest.TestCase):
    """
    15-part Comprehensive Test Suite for Dynamic Story & Master Plan Generation Pipeline.
    Verifies zero hardcoded story templates, protagonist & genre integrity, and provenance metadata.
    """

    def setUp(self):
        self.tmp_dir = tempfile.TemporaryDirectory()
        self.story_dir = Path(self.tmp_dir.name) / "test_story"

    def tearDown(self):
        self.tmp_dir.cleanup()

    def test_1_world_generation_uses_llm(self):
        """TEST 1: Story Director uses LLM and stores LLM_GENERATED provenance metadata."""
        mock_llm = MockDynamicLlamaClient("scifi")
        engine = NovelEngine(self.story_dir, llm_client=mock_llm)
        idea = StoryIdea(title="Vũ Trụ Chi Vương", genre="Khoa học viễn tưởng", protagonist={"name": "Alex Chen", "background": "Kỹ sư không gian"})
        bible = engine.initialize_story(idea)

        self.assertIsNotNone(bible)
        self.assertIn("generation_metadata", bible.model_dump())
        self.assertEqual(bible.generation_metadata["source"], "LLM_GENERATED")
        self.assertFalse(bible.generation_metadata["fallback_used"])

    def test_2_master_plan_uses_llm(self):
        """TEST 2: Master Planner uses LLM and generates dynamic arcs based on Story Bible."""
        mock_llm = MockDynamicLlamaClient("scifi")
        engine = NovelEngine(self.story_dir, llm_client=mock_llm)
        idea = StoryIdea(title="Vũ Trụ Chi Vương", genre="Khoa học viễn tưởng", protagonist={"name": "Alex Chen"})
        engine.initialize_story(idea)

        arcs = engine.generate_master_plan(100)
        self.assertEqual(len(arcs), 2)
        self.assertEqual(arcs[0].title, "Arc 01 — Tín Hiệu Bí Ẩn Nebula")

    def test_3_no_hardcoded_xianxia_fallback(self):
        """TEST 3: Dynamic fallback contains zero hardcoded Xianxia terms."""
        engine = NovelEngine(self.story_dir, llm_client=MockDynamicLlamaClient("failed"))
        idea = StoryIdea(title="Thám Tử Đô Thị", genre="Trinh thám hiện đại", protagonist={"name": "Nguyễn An"})
        bible = engine.initialize_story(idea)

        bible_str = json.dumps(bible.model_dump(), ensure_ascii=False)
        self.assertNotIn("Lâm Phàm", bible_str)
        self.assertNotIn("Thanh Vân Tông", bible_str)
        self.assertNotIn("Tiên Giới", bible_str)
        self.assertNotIn("Trúc Cơ", bible_str)

    def test_4_protagonist_matches_user_idea(self):
        """TEST 4: Protagonist in generated story bible matches idea.protagonist.name."""
        mock_llm = MockDynamicLlamaClient("scifi")
        engine = NovelEngine(self.story_dir, llm_client=mock_llm)
        idea = StoryIdea(title="Chiến Hạm Cygnus", genre="Khoa học viễn tưởng", protagonist={"name": "Alex Chen"})
        bible = engine.initialize_story(idea)

        chars = bible.characters
        self.assertTrue(any(c.get("name") == "Alex Chen" for c in chars))

    def test_5_genre_integrity(self):
        """TEST 5: Non-Xianxia genre rejects LLM output containing Xianxia terms and triggers retry."""
        mock_llm = MockDynamicLlamaClient("injected_xianxia")
        engine = NovelEngine(self.story_dir, llm_client=mock_llm)
        idea = StoryIdea(title="Chiến Hạm Cygnus", genre="Khoa học viễn tưởng", protagonist={"name": "Alex Chen"})
        
        # Engine will reject injected Xianxia output, exhaust retries, and return clean dynamic fallback
        bible = engine.initialize_story(idea)
        bible_str = json.dumps(bible.model_dump(), ensure_ascii=False)
        self.assertNotIn("Lâm Phàm", bible_str)
        self.assertNotIn("Thanh Vân Tông", bible_str)

    def test_6_sci_fi_generation(self):
        """TEST 6: Sci-Fi generation creates space/rank D-C-B concepts."""
        mock_llm = MockDynamicLlamaClient("scifi")
        engine = NovelEngine(self.story_dir, llm_client=mock_llm)
        idea = StoryIdea(title="Vũ Trụ Chi Vương", genre="Khoa học viễn tưởng", protagonist={"name": "Alex Chen"})
        bible = engine.initialize_story(idea)

        self.assertIn("Hành Tinh Alpha-9", bible.world.get("continent_name", ""))
        self.assertTrue(any("Rank D" in cs.get("name", "") for cs in bible.cultivation_system))

    def test_7_detective_generation(self):
        """TEST 7: Detective generation creates case/investigator concepts."""
        mock_llm = MockDynamicLlamaClient("detective")
        engine = NovelEngine(self.story_dir, llm_client=mock_llm)
        idea = StoryIdea(title="Hồ Sơ Mật", genre="Trinh thám hiện đại", protagonist={"name": "Nguyễn An"})
        bible = engine.initialize_story(idea)

        self.assertIn("Thành Phố Sương Mù", bible.world.get("continent_name", ""))
        self.assertTrue(any(c.get("name") == "Nguyễn An" for c in bible.characters))

    def test_8_post_apocalyptic_generation(self):
        """TEST 8: Post-Apocalyptic generation creates wasteland/survival concepts."""
        mock_llm = MockDynamicLlamaClient("post_apocalyptic")
        engine = NovelEngine(self.story_dir, llm_client=mock_llm)
        idea = StoryIdea(title="Thế Giới Phế Tích", genre="Hậu tận thế", protagonist={"name": "Khang"})
        bible = engine.initialize_story(idea)

        self.assertIn("Vùng Đất Phế Tích", bible.world.get("continent_name", ""))
        self.assertTrue(any("Sinh Tồn" in cs.get("description", "") or "Sống Sót" in cs.get("name", "") for cs in bible.cultivation_system))

    def test_9_llm_failure_does_not_inject_static_story(self):
        """TEST 9: LLM failure uses dynamic fallback without static story injection."""
        mock_llm = MockDynamicLlamaClient("failed")
        engine = NovelEngine(self.story_dir, llm_client=mock_llm)
        idea = StoryIdea(title="Robot Chi Vương", genre="Khoa học viễn tưởng", protagonist={"name": "Zero"})
        bible = engine.initialize_story(idea)

        self.assertEqual(bible.generation_metadata["source"], "DYNAMIC_FALLBACK")
        self.assertTrue(bible.generation_metadata["fallback_used"])
        self.assertIn("Zero", bible.characters[0].get("name", ""))

    def test_10_dynamic_fallback_uses_user_idea(self):
        """TEST 10: Dynamic fallback builds strictly from user idea title & genre."""
        mock_llm = MockDynamicLlamaClient("failed")
        engine = NovelEngine(self.story_dir, llm_client=mock_llm)
        idea = StoryIdea(title="Siêu Cấp Thám Tử", genre="Trinh thám", protagonist={"name": "Minh"})
        bible = engine.initialize_story(idea)

        self.assertIn("Siêu Cấp Thám Tử", bible.premise)
        self.assertIn("Trinh thám", bible.premise)

    def test_11_master_plan_not_fixed_25_arcs(self):
        """TEST 11: Master plan arc count adapts dynamically (e.g. 2 arcs, not forced 25)."""
        mock_llm = MockDynamicLlamaClient("scifi")
        engine = NovelEngine(self.story_dir, llm_client=mock_llm)
        idea = StoryIdea(title="Vũ Trụ Chi Vương", genre="Khoa học viễn tưởng", protagonist={"name": "Alex Chen"})
        engine.initialize_story(idea)

        arcs = engine.generate_master_plan(100)
        self.assertEqual(len(arcs), 2)

    def test_12_generation_provenance(self):
        """TEST 12: Provenance metadata records generation source and model correctly."""
        mock_llm = MockDynamicLlamaClient("scifi")
        engine = NovelEngine(self.story_dir, llm_client=mock_llm)
        idea = StoryIdea(title="Vũ Trụ Chi Vương", genre="Khoa học viễn tưởng", protagonist={"name": "Alex Chen"})
        bible = engine.initialize_story(idea)

        meta = bible.generation_metadata
        self.assertEqual(meta["source"], "LLM_GENERATED")
        self.assertEqual(meta["attempt"], 1)

    def test_13_no_static_story_template(self):
        """TEST 13: Entire story bible payload contains zero static story template strings."""
        mock_llm = MockDynamicLlamaClient("detective")
        engine = NovelEngine(self.story_dir, llm_client=mock_llm)
        idea = StoryIdea(title="Vụ Án Không Tên", genre="Trinh thám", protagonist={"name": "Lê Vũ"})
        bible = engine.initialize_story(idea)

        payload_str = json.dumps(bible.model_dump(), ensure_ascii=False)
        self.assertNotIn("Thanh Vân Quả", payload_str)
        self.assertNotIn("Lâm Phàm", payload_str)

    def test_14_world_and_master_plan_are_distinct_per_idea(self):
        """TEST 14: Two distinct story ideas yield completely distinct World and Master Plan payloads."""
        engine1 = NovelEngine(self.story_dir / "story1", llm_client=MockDynamicLlamaClient("scifi"))
        idea1 = StoryIdea(title="Vũ Trụ", genre="Khoa học viễn tưởng", protagonist={"name": "Alex Chen"})
        bible1 = engine1.initialize_story(idea1)

        engine2 = NovelEngine(self.story_dir / "story2", llm_client=MockDynamicLlamaClient("detective"))
        idea2 = StoryIdea(title="Hồ Sơ Mật", genre="Trinh thám", protagonist={"name": "Nguyễn An"})
        bible2 = engine2.initialize_story(idea2)

        self.assertNotEqual(bible1.world["continent_name"], bible2.world["continent_name"])
        self.assertNotEqual(bible1.characters[0]["name"], bible2.characters[0]["name"])

    def test_15_end_to_end_idea_to_master_plan(self):
        """TEST 15: Full end-to-end execution from Idea -> Story Bible -> Master Plan with zero static fallback."""
        mock_llm = MockDynamicLlamaClient("scifi")
        engine = NovelEngine(self.story_dir, llm_client=mock_llm)
        idea = StoryIdea(title="Vũ Trụ Chi Vương", genre="Khoa học viễn tưởng", protagonist={"name": "Alex Chen"})

        bible = engine.initialize_story(idea)
        self.assertEqual(bible.generation_metadata["source"], "LLM_GENERATED")

        arcs = engine.generate_master_plan(100)
        self.assertEqual(len(arcs), 2)
        self.assertEqual(arcs[0].goal, "Alex Chen phát hiện tín hiệu")


if __name__ == "__main__":
    unittest.main()
