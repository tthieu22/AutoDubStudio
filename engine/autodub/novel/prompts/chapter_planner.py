from typing import Dict, Any, List, Optional


class ChapterPlannerPrompt:
    @staticmethod
    def build_prompt(
        chapter_num: int,
        arc_plan: Dict[str, Any],
        open_threads: List[Dict[str, Any]],
        recent_summaries: List[Dict[str, Any]],
        global_ledger: Optional[Any] = None
    ) -> str:
        threads_str = "\n".join([f"- [{t.get('id')}] {t.get('title')} ({t.get('status')})" for t in open_threads]) or "Không có"
        recent_str = "\n".join([f"- Chapter {s.get('chapter_num')}: {s.get('summary_text')}" for s in recent_summaries]) or "Đang ở chương 1"

        ledger_str = "Chưa có tiến triển cũ"
        if global_ledger:
            comp_ev = getattr(global_ledger, "completed_events", []) if hasattr(global_ledger, "completed_events") else global_ledger.get("completed_events", [])
            act_cl = getattr(global_ledger, "active_claims", []) if hasattr(global_ledger, "active_claims") else global_ledger.get("active_claims", [])
            conf_f = getattr(global_ledger, "confirmed_facts", []) if hasattr(global_ledger, "confirmed_facts") else global_ledger.get("confirmed_facts", [])
            ledger_str = f"- Events đã hoàn thành: {comp_ev[-5:]}\n- Confirmed facts: {conf_f[-5:]}\n- Active claims: {act_cl[-5:]}"

        return f"""
=== VAI TRÒ: CHAPTER PLANNER (LẬP KẾ HOẠCH CHƯƠNG TRUYỆN V2.3) ===
Nhiệm vụ: Lập kế hoạch chi tiết cho Chương {chapter_num}.

ARC HIỆN TẠI:
- Tiêu đề Arc: {arc_plan.get('title')}
- Mục tiêu Arc: {arc_plan.get('goal')}
- Xung đột Arc: {arc_plan.get('conflict')}

GLOBAL STORY PROGRESS (CẤM LẶP LẠI SỰ KIỆN/THÔNG TIN ĐÃ CÓ NHƯ DISCOVERY MỚI):
{ledger_str}

CÁC TUYẾN TRUYỆN ĐANG MỞ (OPEN THREADS):
{threads_str}

BỐI CẢNH CÁC CHƯƠNG VỪA QUA:
{recent_str}

QUY TẮC BẮT BUỘC & CẤM LẶP LẠI (ANTI-STAGNATION):
1. CẤM đặt tiêu đề hoặc mục tiêu có cụm từ lặp lại của các chương trước.
2. Chương {chapter_num} PHẢI có sự kiện/địa điểm/hành động HOÀN TOÀN MỚI (Ví dụ: Khai phá vị trí mới, thu thập bằng chứng/tài liệu quan trọng, đối đầu trở ngại mới, giải mã bí mật bối cảnh).
3. Đảm bảo 'goal' chứa một mục tiêu động mang tính hành động cụ thể, tạo ra Narrative Delta rõ ràng so với các chương trước.

[OUTPUT CONTRACT - STRICT RAW JSON ONLY]
- Trả về DUY NHẤT 1 JSON Object hợp lệ.
- CẤM kèm bất kỳ lời dẫn, giải thích hay khối markdown codeblock (```json ... ```).
- ĐẦU RA BẮT ĐẦU BẰNG KÝ TỰ '{' VÀ KẾT THÚC BẰNG '}'.

CẤU TRÚC JSON MẪU:
{{
  "chapter_num": {chapter_num},
  "goal": "Mục tiêu cụ thể mang tính hành động MỚI mà chương này phải đạt được",
  "conflict": "Mâu thuẫn hoặc trở ngại mới xuất hiện trong chương",
  "characters": ["char_001"],
  "reveal": "Bí mật hoặc manh mối mới được hé lộ",
  "ending": "Cái kết mở / Cliffhanger để thu hút chương sau",
  "information_transitions": [
    {{
      "topic": "Tên chủ đề thông tin",
      "from_state": "CLAIM",
      "to_state": "EVIDENCE",
      "method": "Phương pháp xác minh trong chương"
    }}
  ]
}}
"""
