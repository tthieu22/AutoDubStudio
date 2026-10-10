import sys
import os
import shutil
import tempfile
import unittest
from pathlib import Path

# Add autodub engine to sys.path
sys.path.insert(0, str(Path(__file__).parent.parent))

from autodub.novel.novel_models import (
    StoryIdea, CanonCandidate, InformationState, GlobalProgressLedger, NarrativeContract
)
from autodub.novel.novel_database import NovelDatabase
from autodub.novel.canon_validator_engine import CanonValidatorEngine
from autodub.novel.novel_engine import NovelEngine as QwenNovelEngine


class TestNovelV23LocksSuite(unittest.TestCase):
    def setUp(self):
        self.test_dir = Path(tempfile.mkdtemp(prefix="autodub_v23_locks_test_"))
        self.db_path = self.test_dir / "test_story_canon.db"
        self.db = NovelDatabase(db_path=self.db_path)
        self.validator = CanonValidatorEngine(self.db)
        self.story_id = "test_story_locks_001"

        idea = StoryIdea(
            title="Lâm Phàm Truyện",
            genre="Tiên Hiệp",
            style="Audio-First",
            total_chapters=10,
            protagonist={"name": "Lâm Phàm", "age": 18, "background": "Xuyên không"}
        )
        self.db.create_story(self.story_id, idea)

    def tearDown(self):
        if self.test_dir.exists():
            shutil.rmtree(self.test_dir, ignore_errors=True)

    def test_1_semantic_claim_knowledge_leak_fail(self):
        """TEST 1: UNVERIFIED_CLAIM_KNOWLEDGE_LEAK should FAIL when narration asserts active claim as fact."""
        ledger = GlobalProgressLedger(active_claims=["Thanh Vân Quả có nguồn gốc từ Tiên Giới"])
        scene_text = "Lâm Phàm sải bước tiến vào khu vực đệ tử nội môn Thanh Vân Tông và khẳng định biết rằng Thanh Vân Quả có nguồn gốc từ Tiên Giới."
        res = self.validator.validate_scene(self.story_id, 2, 1, scene_text, {"goal": "Test"}, ["char_001"], global_ledger=ledger)
        self.assertFalse(res["passed"], "Should fail due to UNVERIFIED_CLAIM_KNOWLEDGE_LEAK")
        self.assertTrue(any("[UNVERIFIED_CLAIM_KNOWLEDGE_LEAK]" in issue for issue in res["critical_issues"]))

    def test_2_discovery_ignored_fail(self):
        """TEST 2: Chapter ignoring pending discovery should FAIL."""
        ledger = GlobalProgressLedger(pending_discoveries=[{"id": "mysterious_book", "status": "UNTOUCHED"}])
        text = "Lâm Phàm bước vào Thanh Vân Tông. Anh gặp một số đệ tử nội môn và hỏi thăm về nguồn gốc Thanh Vân Quả."
        res = self.validator.validate_chapter_progression(self.story_id, 2, text, global_ledger=ledger)
        self.assertFalse(res["passed"], "Should fail because pending discovery is ignored")

    def test_3_discovery_mentioned_but_not_consumed_fail(self):
        """TEST 3: Discovery mentioned without narrative consequence (not consumed) should FAIL."""
        ledger = GlobalProgressLedger(pending_discoveries=[{"id": "mysterious_book", "status": "UNTOUCHED"}])
        text = "Lâm Phàm nhớ lại cuốn sách bí ẩn. Sau đó anh tiếp tục hỏi đệ tử nội môn về Thanh Vân Quả."
        res = self.validator.validate_chapter_progression(self.story_id, 2, text, global_ledger=ledger)
        self.assertFalse(res["passed"], "Should fail because discovery was only mentioned without consumption consequence")
        self.assertTrue(any("[DISCOVERY_NOT_CONSUMED]" in issue for issue in res["issues"]))

    def test_4_discovery_properly_consumed_pass(self):
        """TEST 4: Discovery properly consumed with narrative consequence should PASS."""
        ledger = GlobalProgressLedger(pending_discoveries=[{"id": "mysterious_book", "status": "UNTOUCHED"}])
        text = "Lâm Phàm mở cuốn sách bí ẩn ra đọc. Anh giải mã được các trang sách cổ và phát hiện ra bằng chứng về Tiên Giới."
        res = self.validator.validate_chapter_progression(self.story_id, 2, text, global_ledger=ledger)
        self.assertTrue(res["passed"], "Should pass when discovery is properly consumed")

    def test_5_same_action_loop_fail(self):
        """TEST 5: Action repetition loop across chapters should FAIL."""
        text = "Lâm Phàm bước vào Thanh Vân Tông, nghe thấy đệ tử nói về Thanh Vân Quả."
        self.db.save_chapter_summary(self.story_id, 1, "Lâm Phàm hỏi đệ tử nội môn về Thanh Vân Quả.", [], [])
        self.db.save_chapter_summary(self.story_id, 2, "Lâm Phàm tiếp tục hỏi đệ tử nội môn về nguồn gốc Thanh Vân Quả.", [], [])
        res = self.validator.validate_chapter_progression(self.story_id, 3, text)
        self.assertFalse(res["passed"], "Should fail due to INFORMATION_OBJECTIVE_LOOP")

    def test_6_semantic_information_loop_different_wording_fail(self):
        """TEST 6: Semantic information loop with different wording should FAIL."""
        self.db.save_chapter_summary(self.story_id, 1, "Lâm Phàm tìm hiểu nguồn gốc trái cây.", [], [])
        self.db.save_chapter_summary(self.story_id, 2, "Lâm Phàm đối chất đệ tử về nguồn gốc trái cây.", [], [])
        text = "Lâm Phàm ván hỏi các trưởng lão về nguồn gốc của linh quả."
        res = self.validator.validate_chapter_progression(self.story_id, 3, text)
        self.assertFalse(res["passed"], "Should fail due to semantic information loop")

    def test_7_unsupported_character_state_fail(self):
        """TEST 7: Asserting ungrounded character state/event should FAIL."""
        ledger = GlobalProgressLedger(completed_events=["Lâm Phàm gia nhập tông môn"])
        text = "Lâm Phàm đứng ở quảng trường. Anh đã hy sinh và cam kết với Tiên Giới."
        res = self.validator.validate_scene(self.story_id, 3, 1, text, {"goal": "Test"}, ["char_001"], global_ledger=ledger)
        self.assertFalse(res["passed"], "Should fail due to UNSUPPORTED_STATE_OR_EVENT")

    def test_8_unsupported_event_transition_fail(self):
        """TEST 8: Asserting ungrounded past event transition should FAIL."""
        ledger = GlobalProgressLedger(completed_events=["Lâm Phàm gia nhập tông môn"])
        text = "Lâm Phàm cảm thấy tự tin vì anh đã đạt được truyền thừa từ Tông chủ."
        res = self.validator.validate_scene(self.story_id, 3, 1, text, {"goal": "Test"}, ["char_001"], global_ledger=ledger)
        self.assertFalse(res["passed"], "Should fail due to ungrounded past event")

    def test_9_npc_extracted_entity_resolution_pass(self):
        """TEST 9: Extracting new NPC and performing entity resolution should PASS."""
        raw_npcs = [{"name": "Thanh Viên", "role_description": "Đệ tử nội môn năng động"}]
        res = self.db.resolve_and_save_npc_candidates(self.story_id, 2, raw_npcs)
        self.assertEqual(len(res), 1)
        self.assertEqual(res[0]["status"], "CREATED_NEW")

        # Verify persisted in DB
        chars = self.db.get_characters(self.story_id)
        self.assertTrue(any(c["name"] == "Thanh Viên" for c in chars))

    def test_10_npc_duplicate_resolution_merge_pass(self):
        """TEST 10: Extracting NPC alias matching existing NPC should MERGE."""
        raw_npcs_1 = [{"name": "Thanh Viên", "role_description": "Đệ tử nội môn"}]
        self.db.resolve_and_save_npc_candidates(self.story_id, 2, raw_npcs_1)

        # Extract alias or full title
        raw_npcs_2 = [{"name": "Thanh Viên đệ tử", "role_description": "Đệ tử nội môn"}]
        res = self.db.resolve_and_save_npc_candidates(self.story_id, 3, raw_npcs_2)
        self.assertEqual(res[0]["status"], "MERGED_EXISTING")

    def test_11_goal_not_completed_fail(self):
        """TEST 11: Chapter failing to fulfill required goals/state delta should FAIL."""
        text = "Lâm Phàm đứng nhìn mây trời. Anh không làm gì cả."
        contract = NarrativeContract(chapter_num=4, required_state_delta={"new_events": 2, "new_information": 2, "evidence": 1})
        res = self.validator.validate_chapter_progression(self.story_id, 4, text, narrative_contract=contract)
        self.assertFalse(res["passed"], "Should fail due to missing required state delta")

    def test_12_required_state_delta_missing_fail(self):
        """TEST 12: Chapter missing mandatory state delta should FAIL."""
        text = "Lâm Phàm đi lại trong phòng."
        contract = NarrativeContract(chapter_num=2, required_state_delta={"new_events": 1, "new_information": 1, "evidence": 1})
        res = self.validator.validate_chapter_progression(self.story_id, 2, text, narrative_contract=contract)
        self.assertFalse(res["passed"])
        self.assertTrue(any("[REQUIRED_STATE_DELTA_MISSING]" in issue for issue in res["issues"]))

    def test_13_valid_chapter_progression_pass(self):
        """TEST 13: Chapter with valid new events, information, and discovery consumption should PASS."""
        ledger = GlobalProgressLedger(pending_discoveries=[{"id": "mysterious_book", "status": "UNTOUCHED"}])
        text = """Lâm Phàm mở cuốn sách bí ẩn ra đọc tỉ mỉ.
Anh giải mã các dòng chữ cổ và tìm thấy bằng chứng độc lập xác nhận thông tin.
Đột nhiên, một nhóm đệ tử Chấp Pháp Đường xuất hiện tiến vào bao vây, tạo ra cuộc đối đầu quyết liệt.
Lâm Phàm quyết định đột phá vòng vây để bảo vệ bằng chứng."""
        res = self.validator.validate_chapter_progression(self.story_id, 1, text, global_ledger=ledger)
        self.assertTrue(res["passed"], "Valid chapter with meaningful progress should pass")

    def test_14_failed_chapter_does_not_commit_memory(self):
        """TEST 14: Failed chapter should NOT update global progress ledger."""
        ledger_before = self.db.get_global_progress_ledger(self.story_id)
        text = "Lâm Phàm đứng nhìn mây trời."
        res = self.validator.validate_chapter_progression(self.story_id, 1, text)
        self.assertFalse(res["passed"])

        ledger_after = self.db.get_global_progress_ledger(self.story_id)
        self.assertEqual(len(ledger_after.completed_events), len(ledger_before.completed_events))

    def test_15_sequential_5_chapter_progression(self):
        """TEST 15: Full 5-Chapter Sequential Story Progression without resets."""
        engine = QwenNovelEngine(story_dir=self.test_dir, story_id=self.story_id)

        # Chapter 1
        ch1_text = """Lâm Phàm bước vào Thanh Vân Tông. Hắn tiến vào Tàng Kinh Các tầng 1 và tìm thấy một cuốn sách bí ẩn chứa thông tin về Tiên Giới."""
        self.db.commit_step_7_memory_transaction(
            story_id=self.story_id,
            chapter_num=1,
            validated_candidates=[],
            global_ledger=GlobalProgressLedger(completed_events=["Khám phá Tàng Kinh Các"], pending_discoveries=[{"id": "cuốn sách bí ẩn", "name": "cuốn sách bí ẩn", "status": "UNTOUCHED"}]),
            summary_text="Lâm Phàm gia nhập tông môn và tìm thấy cuốn sách bí ẩn.",
            key_events=["Khám phá Tàng Kinh Các"],
            char_ids=["char_001"],
            new_threads=[],
            char_changes=[]
        )

        # Chapter 2
        ch2_text = """Lâm Phàm mang cuốn sách bí ẩn về phòng đọc tỉ mỉ và giải mã chữ cổ. Hắn phát hiện ra bằng chứng độc lập ghi nhận nguồn gốc của linh quả."""
        val2 = self.validator.validate_chapter_progression(self.story_id, 2, ch2_text)
        self.assertTrue(val2["passed"], f"Chapter 2 should pass: {val2.get('issues')}")

        # Chapter 3
        self.db.save_chapter_summary(self.story_id, 2, "Lâm Phàm giải mã chữ cổ và ghi nhận bằng chứng.", [], [])
        ch3_text = """Manh mối mới dẫn Lâm Phàm đến Hắc Phong Cốc. Hắn tiến vào cốc trảm sát Ma Thú hung dữ và thu được Yêu Đan thượng phẩm."""
        val3 = self.validator.validate_chapter_progression(self.story_id, 3, ch3_text)
        self.assertTrue(val3["passed"], f"Chapter 3 should pass: {val3.get('issues')}")

        # Chapter 4
        self.db.save_chapter_summary(self.story_id, 3, "Lâm Phàm trảm sát Ma Thú ở Hắc Phong Cốc.", [], [])
        ch4_text = """Trở về tông môn, Lâm Phàm tiến vào Chấp Pháp Đường đối đầu trực tiếp với Trưởng lão. Hắn đưa ra quyết định đột phá cấm chế để bảo vệ bản thân."""
        val4 = self.validator.validate_chapter_progression(self.story_id, 4, ch4_text)
        self.assertTrue(val4["passed"], f"Chapter 4 should pass: {val4.get('issues')}")

        # Chapter 5
        self.db.save_chapter_summary(self.story_id, 4, "Lâm Phàm đối đầu Trưởng lão Chấp Pháp Đường.", [], [])
        ch5_text = """Lâm Phàm thành công đột phá Trúc Cơ Tầng 3 tại Độc Cốc. Hắn giải đáp hoàn toàn nghi vấn cổ xưa và đảo ngược đại cục."""
        val5 = self.validator.validate_chapter_progression(self.story_id, 5, ch5_text)
        self.assertTrue(val5["passed"], f"Chapter 5 should pass: {val5.get('issues')}")

    def test_16_false_progress_detection_fail(self):
        """TEST 16: False Progress (repeating existing facts disguised as new delta) should FAIL."""
        ledger = GlobalProgressLedger(confirmed_facts=["Lâm Phàm gia nhập Thanh Vân Tông và đạt Trúc Cơ Tầng 2"])
        text = "Lâm Phàm gia nhập Thanh Vân Tông và đạt Trúc Cơ Tầng 2."
        res = self.validator.validate_chapter_progression(self.story_id, 2, text, global_ledger=ledger)
        self.assertFalse(res["passed"], "Should fail due to FALSE_PROGRESS_DETECTED")
        self.assertTrue(any("[FALSE_PROGRESS_DETECTED]" in issue for issue in res["issues"]))

    def test_17_reopened_objective_with_new_evidence_pass(self):
        """TEST 17: Reopening old objective when new evidence is present should PASS."""
        self.db.save_chapter_summary(self.story_id, 1, "Lâm Phàm hỏi đệ tử nội môn về nguồn gốc linh quả.", [], [])
        self.db.save_chapter_summary(self.story_id, 2, "Lâm Phàm hỏi trưởng lão về nguồn gốc linh quả.", [], [])
        text = """Lâm Phàm tìm thấy bằng chứng mới cực kỳ quan trọng là bức huyết thư cổ.
Nhờ có bằng chứng mới này, hắn tiếp tục hỏi và đối chất các đệ tử về nguồn gốc linh quả."""
        res = self.validator.validate_chapter_progression(self.story_id, 3, text)
        self.assertTrue(res["passed"], "Reopened objective with new evidence should pass")

    def test_18_deferred_discovery_consumed_later_pass(self):
        """TEST 18: Discovery DEFERRED in Ch 2 and CONSUMED in Ch 4 should PASS."""
        ledger = GlobalProgressLedger(pending_discoveries=[{"id": "cổ thư bí ẩn", "name": "cổ thư bí ẩn", "status": "DEFERRED"}])
        
        # Chapter 2 (Deferred, no consequence) -> Should PASS because status is DEFERRED
        ch2_text = "Lâm Phàm bị bao vây bởi nhóm ma thú. Hắn tạm hoãn việc đọc cổ thư bí ẩn để chiến đấu."
        val2 = self.validator.validate_chapter_progression(self.story_id, 2, ch2_text, global_ledger=ledger)
        self.assertTrue(val2["passed"], "Deferred discovery should pass without forced immediate consumption")

        # Chapter 4 (Consumed with consequence) -> Should PASS
        ch4_text = "Lâm Phàm mở cổ thư bí ẩn ra đọc tỉ mỉ và giải mã các ký tự cổ, tìm ra manh mối Tiên Giới."
        val4 = self.validator.validate_chapter_progression(self.story_id, 4, ch4_text, global_ledger=ledger)
        self.assertTrue(val4["passed"], "Consumed discovery should pass")

    def test_19_npc_alias_stress_resolution_pass(self):
        """TEST 19: Multiple aliases of same NPC should resolve to single canonical entity."""
        raw_1 = [{"name": "Thanh Viên", "role_description": "Đệ tử nội môn"}]
        self.db.resolve_and_save_npc_candidates(self.story_id, 1, raw_1)

        raw_2 = [{"name": "Thanh Viên đệ tử", "role_description": "Đệ tử nội môn"}]
        raw_3 = [{"name": "đệ tử Thanh Viên", "role_description": "Đệ tử nội môn"}]
        raw_4 = [{"name": "Thanh Viên sư huynh", "role_description": "Sư huynh nội môn"}]

        r2 = self.db.resolve_and_save_npc_candidates(self.story_id, 2, raw_2)
        r3 = self.db.resolve_and_save_npc_candidates(self.story_id, 3, raw_3)
        r4 = self.db.resolve_and_save_npc_candidates(self.story_id, 4, raw_4)

        self.assertEqual(r2[0]["status"], "MERGED_EXISTING")
        self.assertEqual(r3[0]["status"], "MERGED_EXISTING")
        self.assertEqual(r4[0]["status"], "MERGED_EXISTING")

        chars = self.db.get_characters(self.story_id)
        self.assertEqual(len(chars), 1, "All 4 aliases should resolve into exactly 1 canonical NPC record")

    def test_20_long_horizon_50_chapter_simulation(self):
        """TEST 20: 50-Chapter Long Horizon progression simulation."""
        locations = ["Tàng Kinh Các tầng 3", "Hắc Phong Cốc thâm sâu", "Chấp Pháp Đường nghiêm mật", "Độc Cốc mờ sương", "Dược Vương Điện cổ kính", "Bát Quái Đàn linh khí", "Tiên Nhân Động bí ẩn"]
        actions = ["giải mã cổ văn", "trảm sát ma thú", "đối đầu trưởng lão", "thu thập linh thảo", "đột phá cảnh giới", "khám phá thạch bia", "xác minh di ngôn"]
        consequences = ["mở ra cơ quan bí mật", "thu được yêu đan thượng phẩm", "thay đổi thái độ môn phái", "tỉnh ngộ thần thông mới", "nhận được cổ thư quý", "định hình tuyến đường mới", "giải đáp ẩn số ngàn năm"]

        for c in range(1, 51):
            loc = locations[c % len(locations)]
            act = actions[c % len(actions)]
            cons = consequences[c % len(consequences)]
            text = f"""Chương {c}: Lâm Phàm một mình đặt chân đến {loc}.
Tại đây, hắn tập trung tinh thần thực hiện {act} nhằm tìm kiếm bằng chứng mới độc lập mang mã số {c}.
Hành động kiên quyết này giúp hắn {cons}, tạo ra bước ngoặt quan trọng cho hành trình."""
            val = self.validator.validate_chapter_progression(self.story_id, c, text)
            self.assertTrue(val["passed"], f"Chapter {c} should pass progression check: {val.get('issues')}")
            self.db.save_chapter_summary(self.story_id, c, f"Chương {c}: Tiến vào {loc}, thực hiện {act} và {cons}.", [], [])


if __name__ == "__main__":
    unittest.main()
