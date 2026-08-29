from typing import Dict, Any, List


class MasterPlannerPrompt:
    @staticmethod
    def build_prompt(story_bible: Dict[str, Any], total_chapters: int = 1000) -> str:
        arcs_count = max(4, min(8, total_chapters // 100))
        premise = story_bible.get('premise', 'Cốt truyện chính')
        prog_ranks = []
        prog_sys = story_bible.get('progression_system', {})
        if isinstance(prog_sys, dict) and 'ranks' in prog_sys and isinstance(prog_sys['ranks'], list):
            prog_ranks = [r.get('name') for r in prog_sys['ranks'] if isinstance(r, dict) and r.get('name')]
        if not prog_ranks:
            prog_ranks = [c.get('name') for c in story_bible.get('cultivation_system', []) if isinstance(c, dict) and c.get('name')]
        
        chaps_per_arc = max(10, total_chapters // arcs_count)

        return f"""=== VAI TRÒ: MASTER PLANNER (KIẾN TRÚC SƯ KỊCH BẢN TỔNG THỂ) ===
Hãy chia bộ truyện dài {total_chapters} chương thành {arcs_count} Arc (Quyển/Tuyến truyện chính).

THÔNG TIN BẢN ĐỒ NỀN MÓNG (STORY BIBLE):
- Tóm tắt cốt truyện: {premise}
- Hệ thống sức mạnh / Cấp độ: {", ".join(prog_ranks) if prog_ranks else "Theo tiến trình câu chuyện"}
- Quy tắc thế giới: {story_bible.get('rules', [])}

⚠️ QUY TẮC BẮT BUỘC:
1. Mỗi Arc đại diện cho 1 giai đoạn phát triển cốt truyện chính, có Mục tiêu (Goal), Xung đột (Conflict), Tiết lộ lớn (Major Reveal), và Sự phát triển nhân vật (Character Development).
2. Tựa đề Arc và nội dung Arc PHẢI bám sát Tiền đề '{premise}'.
3. ĐẦU RA PHẢI LÀ MỘT MẢNG JSON THUẦN TÚY (RAW JSON ARRAY), KHÔNG CÓ BẤT KỲ VĂN BẢN LỜI DẪN NÀO BÊN NGOÀI MẢNG JSON.

MẪU ĐẦU RA YÊU CẦU:
[
  {{
    "arc_num": 1,
    "title": "Arc 01 — Khởi Đầu Vận Mệnh",
    "start_chapter": 1,
    "end_chapter": {chaps_per_arc},
    "goal": "Mục tiêu chính trong Arc 1",
    "conflict": "Xung đột chính trong Arc 1",
    "major_reveal": "Bí mật hoặc phát hiện quan trọng trong Arc 1",
    "character_development": "Sự trưởng thành của nhân vật chính"
  }},
  {{
    "arc_num": 2,
    "title": "Arc 02 — Vươn Tầm Sức Mạnh",
    "start_chapter": {chaps_per_arc + 1},
    "end_chapter": {chaps_per_arc * 2},
    "goal": "Mục tiêu chính trong Arc 2",
    "conflict": "Xung đột chính trong Arc 2",
    "major_reveal": "Bí mật hoặc phát hiện quan trọng trong Arc 2",
    "character_development": "Sự trưởng thành của nhân vật chính"
  }}
]"""
