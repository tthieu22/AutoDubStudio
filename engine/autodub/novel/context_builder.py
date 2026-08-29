import json
import logging
from typing import Dict, Any, List, Optional
from autodub.novel.novel_database import NovelDatabase
from autodub.novel.novel_models import GlobalProgressLedger

logger = logging.getLogger(__name__)


class ContextBuilder:
    """
    Builds token-efficient context window for Qwen2.5 (4K-8K tokens max).
    Handles V2.3 Hierarchical Context Retrieval:
    1. Story Bible
    2. Current Arc
    3. Current Chapter Context
    4. Recent Chapter Summaries
    5. Global Story Progress Ledger
    6. Confirmed Canon
    7. Active Claims (NOT Confirmed)
    8. Evidence Items
    9. Unresolved Questions
    10. Open Threads
    """

    def __init__(self, story_id: str, db: NovelDatabase):
        self.story_id = story_id
        self.db = db

    def build_writer_context(
        self,
        chapter_num: int,
        scene_plan: Dict[str, Any],
        character_ids: List[str],
        global_ledger: Optional[GlobalProgressLedger] = None
    ) -> str:
        if not global_ledger:
            global_ledger = self.db.get_global_progress_ledger(self.story_id)

        # 1. STORY BIBLE (Basic Realm / Rules summary)
        bible_facts = self.db.get_canon_facts(self.story_id, limit=5)
        bible_lines = [f"- {f.get('fact_text')}" for f in bible_facts if f.get("category") in ("world_rule", "realm_change")]
        bible_str = "\n".join(bible_lines) or "- Quy tắc thế giới chuẩn mực"

        # 2. CURRENT ARC
        current_arc = self.db.get_current_arc(self.story_id, chapter_num) or {}
        arc_str = f"Arc #{current_arc.get('arc_num', 1)}: {current_arc.get('title', 'Cốt truyện chính')} (Mục tiêu: {current_arc.get('goal', '')})"

        # 3. CURRENT CHAPTER CONTEXT & CHARACTER STATES
        char_states = []
        know_bounds = []
        for cid in character_ids:
            state = self.db.get_character_state_at_chapter(cid, chapter_num)
            if state:
                name = state.get("name", cid)
                realm = state.get("realm", "Chưa rõ")
                loc = state.get("location", "Chưa rõ")
                known = ", ".join(state.get("known_information", [])[:5]) or "Chưa có"
                char_states.append(f"- {name}: Cảnh giới [{realm}], Vị trí [{loc}]")
                know_bounds.append(f"- {name} ĐÃ BIẾT: [{known}]")
        char_str = "\n".join(char_states) or "- Chưa có dữ liệu nhân vật"
        know_str = "\n".join(know_bounds) or "- Chưa có thông tin giới hạn"

        # 4. RECENT CHAPTER SUMMARIES
        recent_sums = self.db.get_recent_chapter_summaries(self.story_id, chapter_num, count=3)
        sum_lines = [f"- Chương {s['chapter_num']}: {s['summary_text']}" for s in recent_sums]
        sums_str = "\n".join(sum_lines) or "- Chưa có chương trước"

        # 5. GLOBAL STORY PROGRESS LEDGER
        comp_events = global_ledger.completed_events[-5:] if global_ledger.completed_events else []
        events_str = "\n".join([f"- {ev}" for ev in comp_events]) or "- Chưa có sự kiện đã hoàn thành"

        # 6. CONFIRMED CANON
        confirmed = self.db.get_confirmed_facts(self.story_id, limit=8)
        confirmed_lines = [f"- {c.get('fact_text')}" for c in confirmed]
        confirmed_str = "\n".join(confirmed_lines) or "- Chưa có sự thật confirmed"

        # 7. ACTIVE CLAIMS (NOT CONFIRMED)
        claims = self.db.get_active_claims(self.story_id, limit=5)
        claim_lines = [f"- [CLAIM - CHƯA XÁC MINH] Speaker '{c.get('source_speaker', 'NPC')}': {c.get('fact_text')}" for c in claims]
        claims_str = "\n".join(claim_lines) or "- Không có active claims"

        # 8. EVIDENCE ITEMS
        evidence_lines = [f"- [EVIDENCE]: {ev}" for ev in global_ledger.evidence_items[-5:]]
        evidence_str = "\n".join(evidence_lines) or "- Chưa có bằng chứng trực tiếp"

        # 9. UNRESOLVED QUESTIONS
        questions = global_ledger.unresolved_questions[:5]
        questions_str = "\n".join([f"- {q}" for q in questions]) or "- Chưa có câu hỏi mở"

        # 10. OPEN THREADS
        open_threads = self.db.get_open_plot_threads(self.story_id)
        thread_lines = [f"- {t['title']} (từ chương {t['since_chapter']})" for t in open_threads[:5]]
        threads_str = "\n".join(thread_lines) or "- Không có tuyến truyện chưa giải quyết"

        # 11. PENDING DISCOVERIES & MANDATORY CONSUMPTION
        pending_disc = getattr(global_ledger, "pending_discoveries", []) or []
        disc_lines = []
        for d in pending_disc:
            d_id = d.get("id") or d.get("name") or str(d)
            d_status = d.get("status", "UNTOUCHED")
            disc_lines.append(f"- [DISCOVERY]: {d_id} (Trạng thái: {d_status}) -> BẮT BUỘC CONSUMED hoặc DEFERRED ở chương này!")
        disc_str = "\n".join(disc_lines) or "- Không có Discovery treo"

        context = f"""=== 1. STORY BIBLE ===
{bible_str}

=== 2. CURRENT ARC ===
{arc_str}

=== 3. CURRENT CHAPTER & CHARACTER STATES ===
{char_str}
Ranh giới hiểu biết nhân vật:
{know_str}

=== 4. RECENT CHAPTER SUMMARIES ===
{sums_str}

=== 5. PENDING DISCOVERIES & MANDATORY CONSUMPTION (BẮT BUỘC TIÊU THỤ THÔNG TIN/HOOK MỚI) ===
{disc_str}

=== 6. GLOBAL STORY PROGRESS (COMPLETED EVENTS) ===
{events_str}

=== 7. CONFIRMED CANON (SỰ THẬT CHẮC CHẮN) ===
{confirmed_str}

=== 8. ACTIVE CLAIMS — NOT CONFIRMED (LỜI TUYÊN BỐ - CẤM COI LÀ TRUTH) ===
{claims_str}

=== 9. EVIDENCE (BẰNG CHỨNG HIỆN CÓ) ===
{evidence_str}

=== 10. UNRESOLVED QUESTIONS (CÂU HỎI CHƯA GIẢI QUYẾT) ===
{questions_str}

=== 11. OPEN THREADS (TUYẾN TRUYỆN MỞ) ===
{threads_str}""".strip()

        return context

