from typing import Dict, Any, List


class NarrativeContractPrompt:
    @staticmethod
    def build_prompt(
        chapter_num: int,
        chapter_plan: Dict[str, Any],
        context_summary: str,
        open_threads: List[Dict[str, Any]]
    ) -> str:
        goal_text = chapter_plan.get("goal", f"Đạt được mục tiêu chương {chapter_num}") if isinstance(chapter_plan, dict) else str(chapter_plan)

        return f"""=== VAI TRÒ: NARRATIVE CONTRACT GENERATOR (RÀNG BUỘC CỐT TRUYỆN CHƯƠNG {chapter_num} V2.3) ===
Nhiệm vụ: Tạo Hợp đồng Ràng buộc Cốt truyện (Narrative Contract) cho Chương {chapter_num}.
Hợp đồng này quy định những gì BẮT BUỘC xảy ra, những hướng NGHÊM CẤM (Forbidden Topic Drift) và CẤM LẶP LẠI (Forbidden Repetitions).

MỤC TIÊU CHƯƠNG (CHAPTER GOAL):
- {goal_text}

BỐI CẢNH & CANON HIỆN TẠI:
{context_summary}

TUYẾN TRUYỆN MỞ (OPEN THREADS):
{[t.get('title', '') for t in open_threads[:5]]}

[OUTPUT CONTRACT - STRICT RAW JSON ONLY]
- Trả về DUY NHẤT 1 JSON Object hợp lệ theo cấu trúc mẫu sau.
- CẤM kèm bất kỳ lời dẫn, giải thích hay khối markdown codeblock (```json ... ```).
- ĐẦU RA BẮT ĐẦU BẰNG KÝ TỰ '{' VÀ KẾT THÚC BẰNG '}'.

CẤU TRÚC JSON MẪU:
{{
  "chapter_goal": ["{goal_text}"],
  "required_events": ["Sự kiện bắt đầu chương", "Diễn biến chính tạo tiến triển"],
  "required_information": ["Thông tin mới cần tiết lộ"],
  "allowed_characters": ["char_001"],
  "allowed_locations": ["Địa điểm chính"],
  "forbidden_topic_drift": [
    "tranh chấp thương mại",
    "đối tác kinh doanh",
    "tuyến tài nguyên kinh doanh"
  ],
  "forbidden_repetitions": [
    "Không được giới thiệu lại các thông tin/sự kiện đã có trong Canon/Progress như phát hiện mới",
    "Không lặp lại đối thoại xã giao đã hoàn thành",
    "Không biến NPC claims thành confirmed truth mà không có evidence"
  ],
  "information_transitions": [
    {{
      "topic": "Nguồn gốc sự vật/sự kiện",
      "from_state": "CLAIM",
      "to_state": "EVIDENCE"
    }}
  ],
  "character_knowledge_boundaries": {{
    "char_001": ["Không biết trước tương lai", "Không tự bịa lore khi chưa có bằng chứng"]
  }},
  "must_not_change": ["Cảnh giới nhân vật không tự tăng giảm", "Không làm sống lại nhân vật đã chết"]
}}
"""

