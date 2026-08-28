import json
import logging
from typing import Dict, Any, List, Optional
from autodub.novel.novel_database import NovelDatabase
from autodub.novel.novel_models import ScenePlan

logger = logging.getLogger(__name__)


class ContextBuilder:
    """
    Builds token-efficient context window for Qwen2.5-3B (4K-8K tokens max).
    Handles Hybrid Retrieval from SQLite Canon Database.
    """

    def __init__(self, story_id: str, db: NovelDatabase):
        self.story_id = story_id
        self.db = db

    def build_writer_context(self, chapter_num: int, scene_plan: Dict[str, Any], character_ids: List[str]) -> str:
        # 1. World & Cultivation Rules
        current_arc = self.db.get_current_arc(self.story_id, chapter_num) or {}
        arc_str = f"ARC: {current_arc.get('title', 'Unknown')} (Goal: {current_arc.get('goal', '')})"

        # 2. Character States Point-In-Time
        char_states = []
        knowledge_boundaries = []
        for cid in character_ids:
            state = self.db.get_character_state_at_chapter(cid, chapter_num)
            if state:
                name = state.get("name", cid)
                realm = state.get("realm", "Chưa rõ")
                loc = state.get("location", "Chưa rõ")
                known = ", ".join(state.get("known_information", [])[:5]) or "Không có"
                char_states.append(f"- {name}: Cảnh giới [{realm}], Vị trí [{loc}]")
                knowledge_boundaries.append(f"- {name} ĐÃ BIẾT: [{known}]")

        char_str = "\n".join(char_states) or "- Chưa có dữ liệu nhân vật"
        know_str = "\n".join(knowledge_boundaries) or "- Chưa có dữ liệu"

        # 3. Open Plot Threads
        open_threads = self.db.get_open_plot_threads(self.story_id)
        thread_lines = [f"- {t['title']} (từ ch.{t['since_chapter']})" for t in open_threads[:5]]
        threads_str = "\n".join(thread_lines) or "- Không có tuyến truyện chưa giải quyết"

        # 4. Relevant Canon Facts (Hybrid Search)
        keywords = scene_plan.get("goal", "").split() + [c for c in character_ids]
        canon_facts = self.db.query_relevant_context(self.story_id, chapter_num, keywords, limit=10)
        fact_lines = [f"- {f['fact_text']}" for f in canon_facts]
        facts_str = "\n".join(fact_lines) or "- Chưa có canon cũ liên quan"

        # 5. Recent Summaries
        recent_sums = self.db.get_recent_chapter_summaries(self.story_id, chapter_num, count=3)
        sum_lines = [f"- Chương {s['chapter_num']}: {s['summary_text']}" for s in recent_sums]
        sums_str = "\n".join(sum_lines) or "- Không có chương vừa qua"

        context = f"""
1. BỐI CẢNH ARC HIỆN TẠI:
{arc_str}

2. TRẠNG THÁI NHÂN VẬT (CHARACTER STATES):
{char_str}

3. KHIẾN THỨC BẮT BUỘC NẰM TRONG RANH GIỚI (KNOWLEDGE BOUNDARIES):
{know_str}

4. CÁC TUYẾN TRUYỆN MỞ (OPEN THREADS):
{threads_str}

5. CANON NỔI BẬT LƯU TRỮ (RELEVANT CANON):
{facts_str}

6. TÓM TẮT DIỄN BIẾN 3 CHƯƠNG VỪA QUA:
{sums_str}
""".strip()
        return context
