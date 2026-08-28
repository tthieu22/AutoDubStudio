from typing import Dict, Any, List


class ChapterPlannerPrompt:
    @staticmethod
    def build_prompt(
        chapter_num: int,
        arc_plan: Dict[str, Any],
        open_threads: List[Dict[str, Any]],
        recent_summaries: List[Dict[str, Any]]
    ) -> str:
        threads_str = "\n".join([f"- [{t.get('id')}] {t.get('title')} ({t.get('status')})" for t in open_threads]) or "Không có"
        recent_str = "\n".join([f"- Chapter {s.get('chapter_num')}: {s.get('summary_text')}" for s in recent_summaries]) or "Đang ở chương 1"

        return f"""
=== VAI TRÒ: CHAPTER PLANNER (LẬP KẾ HOẠCH CHƯƠNG TRUYỆN) ===
Nhiệm vụ: Lập kế hoạch chi tiết cho Chương {chapter_num}.

ARC HIỆN TẠI:
- Tiêu đề Arc: {arc_plan.get('title')}
- Mục tiêu Arc: {arc_plan.get('goal')}
- Xung đột Arc: {arc_plan.get('conflict')}

CÁC TUYẾN TRUYỆN ĐANG MỞ (OPEN THREADS):
{threads_str}

BỐI CẢNH CÁC CHƯƠNG VỪA QUA:
{recent_str}

YÊU CẦU ĐẦU RA (Trả về JSON Object):
{{
  "chapter_num": {chapter_num},
  "goal": "Mục tiêu cụ thể mà chương này cần đạt được",
  "conflict": "Mẫu thuẫn hoặc trở ngại chính xuất hiện trong chương",
  "characters": ["Tên các nhân vật tham gia chương"],
  "reveal": "Bí mật hoặc thông tin mới được hé lộ (nếu có)",
  "ending": "Cái kết mở / Cliffhanger để thu hút chương sau"
}}
"""
