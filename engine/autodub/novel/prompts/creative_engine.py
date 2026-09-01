from typing import Dict, Any


class CreativeEnginePrompt:
    @staticmethod
    def build_prompt(chapter_num: int, chapter_plan: Dict[str, Any], context_summary: str) -> str:
        return f"""
=== VAI TRÒ: CREATIVE ENGINE (ĐỘNG CƠ SÁNG TẠO & PLOT TWIST) ===
Nhiệm vụ: Trước khi viết Chương {chapter_num}, hãy tạo 3 hướng phát triển tình tiết bất ngờ (Creative Possibilities A, B, C) giúp chương truyện kịch tính, không lặp lại motif nhàm chán.

BỐI CẢNH HIỆN TẠI:
{context_summary}

MỤC TIÊU CHƯƠNG {chapter_num}:
- Goal: {chapter_plan.get('goal')}
- Conflict: {chapter_plan.get('conflict')}

[OUTPUT CONTRACT - STRICT RAW JSON ONLY]
- Trả về DUY NHẤT 1 JSON Object hợp lệ theo cấu trúc mẫu sau.
- CẤM kèm bất kỳ lời dẫn, giải thích hay khối markdown codeblock (```json ... ```).
- ĐẦU RA BẮT ĐẦU BẰNG KÝ TỰ '{' VÀ KẾT THÚC BẰNG '}'.

CẤU TRÚC JSON MẪU:
{{
  "option_a": {{
    "title": "Phương án A — Kịch tính & Phản bội",
    "description": "Tình tiết diễn ra...",
    "impact": "Tác động đến nhân vật..."
  }},
  "option_b": {{
    "title": "Phương án B — Khám phá bí mật quan trọng mới",
    "description": "Tình tiết diễn ra...",
    "impact": "Tác động đến nhân vật..."
  }},
  "option_c": {{
    "title": "Phương án C — Sự cố / Bước ngoặt bất ngờ",
    "description": "Tình tiết diễn ra...",
    "impact": "Tác động đến nhân vật..."
  }},
  "recommended_option": "A",
  "rationale": "Lý do lựa chọn phương án này là..."
}}
"""
