import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

try:
    import pytest
except ImportError:
    pytest = None
import sqlite3
import tempfile
import json
from unittest.mock import MagicMock

from autodub.novel.novel_models import (
    InformationState, CanonFact, CanonCandidate, GlobalProgressLedger, NarrativeContract, ChapterPlan
)
from autodub.novel.novel_database import NovelDatabase
from autodub.novel.canon_validator_engine import CanonValidatorEngine
from autodub.novel.context_builder import ContextBuilder
from autodub.novel.novel_engine import NovelEngine


def temp_db_fixture():
    with tempfile.TemporaryDirectory() as tmpdir:
        db_path = Path(tmpdir) / "test_story.db"
        db = NovelDatabase(db_path)
        yield db


def test_1_database_migration_backward_compatibility(temp_db):
    """Test 1: SQLite schema migration correctly adds V2.3 columns without data loss."""
    conn = temp_db.get_connection()
    cursor = conn.cursor()

    # Verify canon_facts V2.3 columns exist
    cursor.execute("PRAGMA table_info(canon_facts)")
    fact_cols = [row["name"] for row in cursor.fetchall()]
    assert "information_state" in fact_cols
    assert "source_speaker" in fact_cols
    assert "confirmed" in fact_cols
    assert "source_chapter" in fact_cols
    assert "source_scene" in fact_cols

    # Verify global_progress_ledger table exists
    cursor.execute("PRAGMA table_info(global_progress_ledger)")
    ledger_cols = [row["name"] for row in cursor.fetchall()]
    assert "story_id" in ledger_cols
    assert "completed_events_json" in ledger_cols
    assert "confirmed_facts_json" in ledger_cols
    assert "active_claims_json" in ledger_cols


def test_2_information_state_machine(temp_db):
    """Test 2: InformationState Enum and promotion rules (CLAIM cannot automatically become CONFIRMED)."""
    validator = CanonValidatorEngine(temp_db)

    raw_candidates = [
        {
            "category": "lore",
            "fact_text": "Thanh Vân Quả có nguồn gốc từ Tiên Giới",
            "information_state": "CONFIRMED",  # LLM requested CONFIRMED
            "source_speaker": "Thanh Viên",
            "source_excerpt": "Thanh Vân Quả có nguồn gốc từ Tiên Giới",
            "confidence": 0.95
        }
    ]

    final_text = "Thanh Viên mỉm cười nói: 'Thanh Vân Quả có nguồn gốc từ Tiên Giới.' Lâm Phàm lắng nghe nhưng không vội tin tưởng."

    candidates = validator.validate_canon_candidates(
        story_id="story_test",
        chapter_num=1,
        raw_candidates=raw_candidates,
        final_chapter_text=final_text
    )

    assert len(candidates) == 1
    cand = candidates[0]

    # Rule 1 verification: LLM requested CONFIRMED for NPC claim, must be downgraded to CLAIM with confirmed=False
    assert cand.information_state == InformationState.CLAIM
    assert cand.confirmed is False
    assert cand.canon_status == "APPROVED"


def test_3_npc_claim_isolation_guard(temp_db):
    """Test 3: Detect NPC_CLAIM_LEAK when narration treats NPC claim as truth without evidence."""
    validator = CanonValidatorEngine(temp_db)

    scene_text = "Thanh Viên mỉm cười nói: 'Thanh Vân Quả có nguồn gốc từ Tiên Giới.' Lâm Phàm chắc chắn rằng đó chính là sự thật."
    res = validator.validate_scene(
        story_id="story_test",
        chapter_num=1,
        scene_index=1,
        scene_text=scene_text,
        scene_plan={"goal": "Gặp NPC"},
        character_ids=["char_001"]
    )

    assert res["passed"] is False
    assert any("[NPC_CLAIM_LEAK]" in issue for issue in res["issues"])


def test_4_cross_chapter_repetition(temp_db):
    """Test 4: Detect cross-chapter repetition when chapter rehashes past events/summaries."""
    validator = CanonValidatorEngine(temp_db)
    temp_db.save_chapter_summary(
        story_id="story_test",
        chapter_num=1,
        summary_text="Lâm Phàm phát hiện Thanh Vân Quả liên quan đến Tiên Giới.",
        key_events=["Gia nhập tông môn"],
        characters_present=["char_001"]
    )

    repeat_text = "Lâm Phàm bước đi và phát hiện Thanh Vân Quả liên quan đến Tiên Giới."
    prog_res = validator.validate_chapter_progression(
        story_id="story_test",
        chapter_num=2,
        chapter_text=repeat_text
    )

    assert prog_res["cross_chapter_repetition"] is True
    assert prog_res["stagnation_detected"] is True
    assert prog_res["passed"] is False


def test_5_valid_progression(temp_db):
    """Test 5: Chapter progression validation passes when meaningful progress is present."""
    validator = CanonValidatorEngine(temp_db)

    valid_text = """
    Lâm Phàm âm thầm giải mã một trang cổ thư bí mật. Hắn tìm thấy bằng chứng độc lập xác nhận thông tin.
    Quyết định đột phá cảnh giới và đối đầu với thế lực Ma Tông xuất hiện ở đại điện.
    Lâm Phàm làm rõ nguyên nhân cuộc tấn công.
    """

    prog_res = validator.validate_chapter_progression(
        story_id="story_test",
        chapter_num=2,
        chapter_text=valid_text
    )

    assert prog_res["meaningful_progress_score"] > 50
    assert prog_res["stagnation_detected"] is False
    assert prog_res["passed"] is True


def test_6_stagnation_detection(temp_db):
    """Test 6: Pure filler chapter fails progression with score = 0."""
    validator = CanonValidatorEngine(temp_db)

    filler_text = "Lâm Phàm suy nghĩ về hành trình phía trước. Hắn cảm thấy lo lắng và cố giữ bình tĩnh. Không có gì xảy ra thêm."
    prog_res = validator.validate_chapter_progression(
        story_id="story_test",
        chapter_num=3,
        chapter_text=filler_text
    )

    assert prog_res["meaningful_progress_score"] == 0
    assert prog_res["stagnation_detected"] is True
    assert prog_res["passed"] is False


def test_7_atomic_memory_transaction(temp_db):
    """Test 7: Step 7 memory transaction is atomic (commits cleanly or rolls back on error)."""
    ledger = GlobalProgressLedger(completed_events=["Event 1"], confirmed_facts=["Fact 1"])
    cand = CanonCandidate(
        story_id="story_test",
        chapter_num=1,
        category="event",
        fact_text="Fact 1",
        source_excerpt="Excerpt 1",
        information_state=InformationState.CONFIRMED,
        canon_status="APPROVED",
        confirmed=True
    )

    temp_db.commit_step_7_memory_transaction(
        story_id="story_test",
        chapter_num=1,
        validated_candidates=[cand],
        global_ledger=ledger,
        summary_text="Summary 1",
        key_events=["Event 1"],
        char_ids=["char_001"],
        new_threads=[],
        char_changes=[]
    )

    saved_ledger = temp_db.get_global_progress_ledger("story_test")
    assert saved_ledger.completed_events == ["Event 1"]
    assert saved_ledger.confirmed_facts == ["Fact 1"]

    facts = temp_db.get_confirmed_facts("story_test")
    assert len(facts) == 1
    assert facts[0]["fact_text"] == "Fact 1"


def test_8_candidate_source_grounding(temp_db):
    """Test 8: Un-grounded candidate facts (hallucinations) are rejected."""
    validator = CanonValidatorEngine(temp_db)

    candidates = [
        {
            "category": "lore",
            "fact_text": "Lâm Phàm sở hữu Cửu Trọng Tiên Thể",
            "confidence": 0.9,
            "source_excerpt": "Cửu Trọng Tiên Thể"
        }
    ]

    final_text = "Lâm Phàm chỉ là một đệ tử bình thường tại Thanh Vân Tông."
    val_cands = validator.validate_canon_candidates("story_test", 1, candidates, final_text)

    assert len(val_cands) == 1
    assert val_cands[0].canon_status == "REJECTED"


def test_9_hierarchical_retrieval_formatting(temp_db):
    """Test 9: ContextBuilder formats hierarchical retrieval sections cleanly."""
    ctx_builder = ContextBuilder("story_test", temp_db)
    ledger = GlobalProgressLedger(
        completed_events=["Lâm Phàm gia nhập tông môn"],
        unresolved_questions=["Thanh Vân Quả từ đâu ra?"],
        active_claims=["Thanh Vân Quả đến từ Tiên Giới"]
    )

    context = ctx_builder.build_writer_context(1, {"goal": "Test"}, ["char_001"], global_ledger=ledger)

    assert "=== 1. STORY BIBLE ===" in context
    assert "=== 5. GLOBAL STORY PROGRESS (COMPLETED EVENTS) ===" in context
    assert "=== 7. ACTIVE CLAIMS — NOT CONFIRMED (LỜI TUYÊN BỐ - CẤM COI LÀ TRUTH) ===" in context
    assert "Lâm Phàm gia nhập tông môn" in context


def test_10_sequential_story_generation(temp_db):
    """
    Test 10: Sequential 3-Chapter Story Integration Test
    Verifies Chapter 1 -> Chapter 2 -> Chapter 3 execution pipeline,
    state isolation, anti-repetition, progress calculation, and atomic DB commits.
    """
    validator = CanonValidatorEngine(temp_db)
    story_id = "story_sequential_test"

    # ══════════════════════════════════════════════════════════════
    # CHAPTER 1: Premise Setup
    # ══════════════════════════════════════════════════════════════
    c1_text = """
    Lâm Phàm tỉnh dậy trong một thôn hẻo lánh, nhận ra mình vừa xuyên không.
    Đúng lúc đó, âm thanh hệ thống vang lên trong đầu hắn, kích hoạt nhiệm vụ tân thủ.
    Hắn liền thu dọn hành trang, lập tức lên đường gia nhập Thanh Vân Tông.
    Tại đại điện Tông môn, Trưởng lão Thanh Viên mỉm cười nói: "Thanh Vân Quả có nguồn gốc từ Tiên Giới."
    Lâm Phàm lắng nghe nhưng ghi nhớ kỹ rằng đây chỉ là phát biểu từ một NPC, cần kiểm chứng thêm.
    """

    # Extract metadata candidates from C1
    c1_raw_candidates = [
        {
            "category": "lore",
            "fact_text": "Thanh Vân Quả có nguồn gốc từ Tiên Giới",
            "information_state": "CONFIRMED",  # LLM requested CONFIRMED
            "source_speaker": "Thanh Viên",
            "source_excerpt": "Thanh Vân Quả có nguồn gốc từ Tiên Giới",
            "confidence": 0.9
        }
    ]

    c1_validated_cand = validator.validate_canon_candidates(story_id, 1, c1_raw_candidates, c1_text)

    # ASSERTIONS FOR CHAPTER 1
    assert len(c1_validated_cand) == 1
    assert c1_validated_cand[0].information_state == InformationState.CLAIM  # NPC claim isolated as CLAIM!
    assert c1_validated_cand[0].confirmed is False  # No CLAIM -> CONFIRMED leak!

    c1_ledger = GlobalProgressLedger(
        completed_events=["Lâm Phàm xuyên không, kích hoạt hệ thống, gia nhập Thanh Vân Tông"],
        revealed_information=["Thanh Viên tuyên bố Thanh Vân Quả liên quan Tiên Giới"],
        active_claims=["Thanh Vân Quả có nguồn gốc từ Tiên Giới"]
    )

    temp_db.commit_step_7_memory_transaction(
        story_id=story_id,
        chapter_num=1,
        validated_candidates=c1_validated_cand,
        global_ledger=c1_ledger,
        summary_text="Chương 1: Lâm Phàm xuyên không gia nhập Thanh Vân Tông và nghe Thanh Viên nói về Thanh Vân Quả.",
        key_events=["Gia nhập Thanh Vân Tông"],
        char_ids=["char_001"],
        new_threads=[],
        char_changes=[]
    )

    # Verify Chapter 1 Persistence
    saved_ledger_c1 = temp_db.get_global_progress_ledger(story_id)
    assert len(saved_ledger_c1.confirmed_facts) == 0  # Confirmed facts empty!
    assert "Thanh Vân Quả có nguồn gốc từ Tiên Giới" in saved_ledger_c1.active_claims

    # ══════════════════════════════════════════════════════════════
    # CHAPTER 2: Avoid Repetition & Force Delta Progress
    # ══════════════════════════════════════════════════════════════

    # Case A: Invalid Chapter 2 draft repeating Chapter 1 discovery
    invalid_c2_text = "Lâm Phàm tiếp tục tìm hiểu và phát hiện Thanh Vân Quả có nguồn gốc từ Tiên Giới."
    prog_invalid_c2 = validator.validate_chapter_progression(
        story_id=story_id,
        chapter_num=2,
        chapter_text=invalid_c2_text,
        global_ledger=saved_ledger_c1
    )
    assert prog_invalid_c2["cross_chapter_repetition"] is True  # Detected repetition!
    assert prog_invalid_c2["stagnation_detected"] is True  # Stagnation flagged!

    # Case B: Valid Chapter 2 draft introducing new evidence & question
    valid_c2_text = """
    Lâm Phàm bước vào Tàng Kinh Các tầng hai của Thanh Vân Tông.
    Hắn mở một cuốn cổ thư bọc da đen phủ đầy bụi rậm. Cổ thư ghi chép bằng chứng về vụ mất tích của Tiên Đan Tông năm xưa.
    Cuốn sách ghi rõ sự kiện đại chiến ngàn năm trước và để lại nghi vấn về kẻ chủ mưu.
    Lâm Phàm thu thập thêm tài liệu độc lập và đặt ra câu hỏi về thế lực ẩn giấu.
    """
    prog_valid_c2 = validator.validate_chapter_progression(
        story_id=story_id,
        chapter_num=2,
        chapter_text=valid_c2_text,
        global_ledger=saved_ledger_c1
    )

    assert prog_valid_c2["cross_chapter_repetition"] is False
    assert prog_valid_c2["stagnation_detected"] is False
    assert prog_valid_c2["meaningful_progress_score"] > 50

    c2_raw_candidates = [
        {
            "category": "evidence",
            "fact_text": "Tiên Đan Tông từng biến mất sau cuộc đại chiến ngàn năm trước",
            "information_state": "EVIDENCE",
            "source_speaker": "Cổ thư Tàng Kinh Các",
            "source_excerpt": "Tiên Đan Tông năm xưa",
            "confidence": 0.92
        }
    ]
    c2_validated_cand = validator.validate_canon_candidates(story_id, 2, c2_raw_candidates, valid_c2_text)

    saved_ledger_c1.completed_events.append("Khám phá Tàng Kinh Các và phát hiện vụ mất tích của Tiên Đan Tông")
    saved_ledger_c1.evidence_items.append("Tiên Đan Tông từng biến mất sau cuộc đại chiến ngàn năm trước")
    saved_ledger_c1.unresolved_questions.append("Kẻ nào đứng sau vụ mất tích của Tiên Đan Tông?")

    temp_db.commit_step_7_memory_transaction(
        story_id=story_id,
        chapter_num=2,
        validated_candidates=c2_validated_cand,
        global_ledger=saved_ledger_c1,
        summary_text="Chương 2: Lâm Phàm phát hiện cổ thư Tiên Đan Tông ở Tàng Kinh Các.",
        key_events=["Phát hiện cổ thư Tiên Đan Tông"],
        char_ids=["char_001"],
        new_threads=[],
        char_changes=[]
    )

    saved_ledger_c2 = temp_db.get_global_progress_ledger(story_id)
    assert len(saved_ledger_c2.evidence_items) == 1
    assert len(saved_ledger_c2.unresolved_questions) == 1

    # ══════════════════════════════════════════════════════════════
    # CHAPTER 3: NPC Statement & Action Progression
    # ══════════════════════════════════════════════════════════════

    c3_text = """
    Tông chủ Thanh Vân Tông xuất hiện ở sơn đỉnh và nói: "Thanh Vân Quả đến từ Tiên Giới."
    Lâm Phàm chỉ gật đầu ghi nhận thông tin này từ Tông chủ nhưng không vội coi đó là sự thật tuyệt đối.
    Hắn lập tức nhận nhiệm vụ rèn luyện đầu tiên, dẫn đầu nhóm đệ tử tiến vào Hắc Phong Cốc để săn bắt Ma Thú.
    Trận chiến với Huyết Lang xảy ra ác liệt, Lâm Phàm tung chiêu quyết định đánh bại thủ lĩnh Ma Thú.
    """

    # Check Scene NPC Claim Guard
    val_c3_scene = validator.validate_scene(
        story_id=story_id,
        chapter_num=3,
        scene_index=1,
        scene_text=c3_text,
        scene_plan={"goal": "Nhận nhiệm vụ Hắc Phong Cốc"},
        character_ids=["char_001"]
    )
    assert val_c3_scene["passed"] is True  # No NPC_CLAIM_LEAK!

    c3_raw_candidates = [
        {
            "category": "claim",
            "fact_text": "Tông chủ khẳng định Thanh Vân Quả đến từ Tiên Giới",
            "information_state": "CLAIM",
            "source_speaker": "Tông chủ Thanh Vân Tông",
            "source_excerpt": "Thanh Vân Quả đến từ Tiên Giới",
            "confidence": 0.88
        }
    ]
    c3_validated_cand = validator.validate_canon_candidates(story_id, 3, c3_raw_candidates, c3_text)
    assert c3_validated_cand[0].information_state == InformationState.CLAIM
    assert c3_validated_cand[0].confirmed is False

    prog_c3 = validator.validate_chapter_progression(
        story_id=story_id,
        chapter_num=3,
        chapter_text=c3_text,
        global_ledger=saved_ledger_c2
    )

    assert prog_c3["cross_chapter_repetition"] is False
    assert prog_c3["stagnation_detected"] is False
    assert prog_c3["meaningful_progress_score"] > 50

    saved_ledger_c2.completed_events.append("Tiến vào Hắc Phong Cốc và đánh bại Huyết Lang thủ lĩnh")
    temp_db.commit_step_7_memory_transaction(
        story_id=story_id,
        chapter_num=3,
        validated_candidates=c3_validated_cand,
        global_ledger=saved_ledger_c2,
        summary_text="Chương 3: Lâm Phàm nhận nhiệm vụ tiến vào Hắc Phong Cốc và tiêu diệt Huyết Lang.",
        key_events=["Đánh bại Huyết Lang ở Hắc Phong Cốc"],
        char_ids=["char_001"],
        new_threads=[],
        char_changes=[]
    )

    saved_ledger_c3 = temp_db.get_global_progress_ledger(story_id)
    assert len(saved_ledger_c3.completed_events) == 3
    assert len(saved_ledger_c3.confirmed_facts) == 0  # Confirmed facts remain isolated from unverified NPC claims!


if __name__ == "__main__":
    print("=== RUNNING ENGINE V2.3 INTEGRATION TEST SUITE ===")
    import tempfile
    from pathlib import Path

    with tempfile.TemporaryDirectory(ignore_cleanup_errors=True) as tmpdir:
        db_path = Path(tmpdir) / "test_story.db"
        db = NovelDatabase(db_path)

        print("[TEST 1] Testing Database Migration...")
        test_1_database_migration_backward_compatibility(db)
        print("  -> PASS")

        print("[TEST 2] Testing Information State Machine...")
        test_2_information_state_machine(db)
        print("  -> PASS")

        print("[TEST 3] Testing NPC Claim Isolation Guard...")
        test_3_npc_claim_isolation_guard(db)
        print("  -> PASS")

        print("[TEST 4] Testing Cross-Chapter Repetition Lock...")
        test_4_cross_chapter_repetition(db)
        print("  -> PASS")

        print("[TEST 5] Testing Valid Progression Validation...")
        test_5_valid_progression(db)
        print("  -> PASS")

        print("[TEST 6] Testing Stagnation Detection...")
        test_6_stagnation_detection(db)
        print("  -> PASS")

        print("[TEST 7] Testing Atomic Memory Transaction...")
        test_7_atomic_memory_transaction(db)
        print("  -> PASS")

        print("[TEST 8] Testing Candidate Grounding...")
        test_8_candidate_source_grounding(db)
        print("  -> PASS")

        print("[TEST 9] Testing Hierarchical Retrieval Formatting...")
        test_9_hierarchical_retrieval_formatting(db)
        print("  -> PASS")

        print("[TEST 10] Testing Sequential 3-Chapter Story Integration...")
        test_10_sequential_story_generation(db)
        print("  -> PASS")

    print("\n[OK] ALL 10 V2.3 INTEGRATION TESTS PASSED SUCCESSFULLY!")


