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

YÊU CẦU ĐẦU RA (Trả về JSON Object):
{{
  "option_a": {{
    "title": "Phương án A — Kịch tính & Phản bội",
    "description": "Tình tiết diễn ra...",
    "impact": "Tác động đến nhân vật..."
  }},
  "option_b": {{
    "title": "Phương án B — Phát hiện bí mật thượng cổ",
    "description": "Tình tiết diễn ra...",
    "impact": "Tác động đến nhân vật..."
  }},
  "option_c": {{
    "title": "Phương án C — Nhiệm vụ hệ thống bất thường",
    "description": "Tình tiết diễn ra...",
    "impact": "Tác động đến nhân vật..."
  }},
  "recommended_option": "A",
  "rationale": "Lý do lựa chọn phương án này là..."
}}
"""
