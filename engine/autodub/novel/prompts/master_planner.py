from typing import Dict, Any, List


class MasterPlannerPrompt:
    @staticmethod
    def build_prompt(story_bible: Dict[str, Any], total_chapters: int = 1000) -> str:
        arcs_count = max(5, min(30, total_chapters // 40))
        return f"""
=== VAI TRÒ: MASTER PLANNER (KIẾN TRÚC SƯ KỊCH BẢN TỔNG THỂ) ===
Hãy chia bộ truyện dài {total_chapters} chương thành {arcs_count} Arc (Quyển/Tuyến truyện chính).

STORY BIBLE THAM KHẢO:
- Tiền đề: {story_bible.get('premise', '')}
- Cảnh giới: {[c.get('name') for c in story_bible.get('cultivation_system', [])]}
- Quy tắc: {story_bible.get('rules', [])}

YÊU CẦU ĐẦU RA (Trả về duy nhất JSON Array các Arc Plan):
[
  {{
    "arc_num": 1,
    "title": "Arc 01 — Xuyên Không & Gia Nhập Thanh Vân Tông",
    "start_chapter": 1,
    "end_chapter": 40,
    "goal": "Lâm Phàm xuyên không, kích hoạt hệ thống và vượt qua khảo nghiệm gia nhập Thanh Vân Tông",
    "conflict": "Bị nội môn đệ tử chèn ép và đối đầu yêu thú ranh giới bí cảnh",
    "major_reveal": "Phát hiện hệ thống có thể thu thập linh khí phế thải",
    "character_development": "Từ thận trọng sợ chết chuyển sang tự tin làm chủ sức mạnh"
  }},
  {{
    "arc_num": 2,
    "title": "Arc 02 — Bí Cảnh Tinh Hà & Đột Phá Trúc Cơ",
    "start_chapter": 41,
    "end_chapter": 80,
    "goal": "Tìm kiếm Tinh Hà Quả để đột phá Trúc Cơ",
    "conflict": "Ma Tông vây bắt đệ tử Thanh Vân Tông trong bí cảnh",
    "major_reveal": "Sư phụ có quan hệ bí mật với Ma Tông Trưởng lão",
    "character_development": "Học cách ẩn nhẫn và dụng mưu đánh bại kẻ thù mạnh hơn"
  }}
]
"""
