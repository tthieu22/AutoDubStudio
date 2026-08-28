import os
import tempfile
import unittest
from autodub.novel.novel_models import (
    StoryIdea, Character, CharacterState, CanonFact, PlotThread, ArcPlan
)
from autodub.novel.novel_database import NovelDatabase


class TestNovelDatabase(unittest.TestCase):
    def test_novel_database_init_and_crud(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            db_path = os.path.join(tmp_dir, "test_story.db")
            db = NovelDatabase(db_path)

            # 1. Test Story creation
            idea = StoryIdea(
                title="Thần Ma Tiên Đế",
                genre="Tiên hiệp + Xuyên không",
                style="Tiết tấu nhanh",
                total_chapters=500
            )
            db.create_story("story_001", idea)

            # 2. Test Character & State
            char = Character(
                id="char_001",
                name="Lâm Phàm",
                personality=["Thận trọng", "Thông minh"],
                goal="Trở thành Tiên Đế",
                realm="Luyện Khí Tầng 1",
                location="Thanh Vân Tông"
            )
            db.save_character(char, "story_001")

            state = CharacterState(
                character_id="char_001",
                chapter_num=10,
                realm="Trúc Cơ Sơ Kỳ",
                location="Bí Cảnh Thanh Vân",
                relationships={"char_002": "Sư huynh"},
                known_information=["Thanh Vân Tông có nội gián"]
            )
            db.update_character_state(state)

            fetched_state = db.get_character_state_at_chapter("char_001", 10)
            self.assertIsNotNone(fetched_state)
            self.assertEqual(fetched_state["realm"], "Trúc Cơ Sơ Kỳ")
            self.assertEqual(fetched_state["location"], "Bí Cảnh Thanh Vân")
            self.assertIn("char_002", fetched_state["relationships"])

            # 3. Test Canon Facts
            fact = CanonFact(
                story_id="story_001",
                chapter_num=10,
                category="realm_change",
                fact_text="Lâm Phàm đột phá Trúc Cơ nhờ Thanh Vân Quả",
                source="chapter_content"
            )
            fact_id = db.insert_canon_fact(fact)
            self.assertGreater(fact_id, 0)

            facts = db.get_canon_facts("story_001", limit=10)
            self.assertEqual(len(facts), 1)
            self.assertIn("Thanh Vân Quả", facts[0]["fact_text"])

            # 4. Test Plot Thread
            thread = PlotThread(
                id="thread_001",
                story_id="story_001",
                title="Sư phụ mất tích",
                status="OPEN",
                since_chapter=5,
                description="Sư phụ Lý Thanh Vân đi bí cảnh chưa về"
            )
            db.save_plot_thread(thread)

            open_threads = db.get_open_plot_threads("story_001")
            self.assertEqual(len(open_threads), 1)
            self.assertEqual(open_threads[0]["title"], "Sư phụ mất tích")

            # 5. Test Arc Plan
            arc = ArcPlan(
                id="arc_01",
                story_id="story_001",
                arc_num=1,
                title="Thanh Vân Tông Phong Vân",
                start_chapter=1,
                end_chapter=50,
                goal="Gia nhập Thanh Vân Tông và đạt Trúc Cơ",
                conflict="Trưởng lão Ma Tông cài nội gián",
                major_reveal="Sư phụ là Cửu Trọng Thiên cao thủ",
                status="PLANNED"
            )
            db.save_arc_plans([arc])

            current_arc = db.get_current_arc("story_001", chapter_num=25)
            self.assertIsNotNone(current_arc)
            self.assertEqual(current_arc["title"], "Thanh Vân Tông Phong Vân")


if __name__ == "__main__":
    unittest.main()
