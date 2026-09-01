from typing import Dict, Any, List


class MasterPlannerPrompt:
    @staticmethod
    def build_prompt(story_bible: Dict[str, Any], total_chapters: int = 1000) -> str:
        # Scale Arcs dynamically (~20 chapters per Arc for smooth pacing & rich plot structure)
        chaps_per_arc = 20
        arcs_count = max(5, min(50, (total_chapters + chaps_per_arc - 1) // chaps_per_arc))

        premise = story_bible.get('premise', 'Cốt truyện chính')
        prog_ranks = []
        prog_sys = story_bible.get('progression_system', {})
        if isinstance(prog_sys, dict) and 'ranks' in prog_sys and isinstance(prog_sys['ranks'], list):
            prog_ranks = [r.get('name') for r in prog_sys['ranks'] if isinstance(r, dict) and r.get('name')]
        if not prog_ranks:
            prog_ranks = [c.get('name') for c in story_bible.get('cultivation_system', []) if isinstance(c, dict) and c.get('name')]
        
        return f"""=== VAI TRÒ: MASTER PLANNER (KIẾN TRÚC SƯ KỊCH BẢN TỔNG THỂ DÀI HẠN) ===
Nhiệm vụ: Hãy phân bổ bộ truyện dài {total_chapters} chương thành chuỗi {arcs_count} Arc (Quyển/Tuyến truyện liên hoàn). Mỗi Arc kéo dài khoảng {chaps_per_arc} chương để đảm bảo cốt truyện dày dặn, cao trào liên tục và không bị lặp.

THÔNG TIN BẢN ĐỒ NỀN MÓNG (STORY BIBLE):
- Tóm tắt cốt truyện: {premise}
- Hệ thống sức mạnh / Cấp độ: {", ".join(prog_ranks) if prog_ranks else "Theo tiến trình câu chuyện"}
- Quy tắc thế giới: {story_bible.get('rules', [])}

QUY TẮC BẮT BUỘC:
1. Chia đủ {arcs_count} Arc nối tiếp nhau từ Chương 1 đến Chương {total_chapters}.
2. Mỗi Arc có Mục tiêu (Goal), Xung đột (Conflict), Phát hiện lớn (Major Reveal), và Phát triển nhân vật (Character Development) riêng biệt.
3. Tựa đề Arc và nội dung Arc PHẢI bám sát Tiền đề '{premise}'.
4. TOÀN BỘ NỘI DUNG (Tựa đề Arc, Mục tiêu, Xung đột, Phát hiện lớn, Phát triển nhân vật) PHẢI VIẾT HOÀN TOÀN BẰNG TIẾNG VIỆT 100% (CẤM dùng tiếng Anh hoặc tiếng Trung).

[OUTPUT CONTRACT - STRICT RAW JSON ONLY]
- Trả về DUY NHẤT 1 Mảng JSON (JSON Array) hợp lệ.
- CẤM kèm bất kỳ lời dẫn, giải thích hay khối markdown codeblock (```json ... ```).
- ĐẦU RA BẮT ĐẦU BẰNG KÝ TỰ '[' VÀ KẾT THÚC BẰNG ']'.

CẤU TRÚC JSON MẪU:
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

    @staticmethod
    def build_batch_prompt(
        story_bible: Dict[str, Any], 
        total_chapters: int,
        batch_start: int, 
        batch_end: int,
        chaps_per_arc: int = 20,
        previous_arcs: List[Dict[str, Any]] = None
    ) -> str:
        """Build a rich, contextual prompt for generating a specific batch of arcs with unique titles and plot progression."""
        premise = story_bible.get('premise', 'Cốt truyện chính')
        
        # Extract detailed world context
        world_obj = story_bible.get('world', {}) if isinstance(story_bible.get('world'), dict) else {}
        locations = world_obj.get('locations', [])
        locations_str = ", ".join([loc if isinstance(loc, str) else loc.get("name", "") for loc in locations]) if locations else "Thiên Đô Tông, Kinh Thành Thiên Đô, Trạm Vũ Trụ Hắc Ám"
        
        factions = world_obj.get('factions', [])
        factions_str = ", ".join([fac if isinstance(fac, str) else fac.get("name", "") for fac in factions]) if factions else "Thiên Đô Tông, Thiên Đô Phản Diện"

        chars = story_bible.get('characters', [])
        chars_str = ", ".join([c.get("name", "") for c in chars if isinstance(c, dict) and c.get("name")]) if chars else "Diệp Phàm, Nguyệt Nhi, Trần Phong, Hương Nhi"

        prog_ranks = []
        prog_sys = story_bible.get('progression_system', {})
        if isinstance(prog_sys, dict) and 'ranks' in prog_sys and isinstance(prog_sys['ranks'], list):
            prog_ranks = [r.get('name') for r in prog_sys['ranks'] if isinstance(r, dict) and r.get('name')]
        if not prog_ranks:
            prog_ranks = [c.get('name') for c in story_bible.get('cultivation_system', []) if isinstance(c, dict) and c.get('name')]
        ranks_str = ", ".join(prog_ranks) if prog_ranks else "Cấp 1 Khởi Đầu -> Cấp 10 Đỉnh Phong"

        batch_count = batch_end - batch_start + 1
        start_chapter = (batch_start - 1) * chaps_per_arc + 1
        end_chapter = min(batch_end * chaps_per_arc, total_chapters)

        # Build summary of previous arcs for context continuity
        prev_summary = ""
        if previous_arcs and len(previous_arcs) > 0:
            prev_titles = []
            for a in previous_arcs[-5:]:  # Last 5 arcs for context
                if isinstance(a, dict):
                    t = a.get("title", f"Arc {a.get('arc_num', '?')}")
                    g = a.get("goal", "")
                    prev_titles.append(f"  - Arc {a.get('arc_num', '?')}: {t} | Mục tiêu: {g}")
            if prev_titles:
                prev_summary = f"""
CÁC ARC ĐÃ TẠO TRƯỚC ĐÓ (Tiếp nối trực tiếp mạch truyện):
{chr(10).join(prev_titles)}
"""

        return f"""=== VAI TRÒ: MASTER PLANNER (BATCH — Tạo Arc {batch_start} đến {batch_end}) ===
Nhiệm vụ: Hãy sáng tạo kịch bản chi tiết cho {batch_count} Arc (từ Arc {batch_start:02d} đến Arc {batch_end:02d}) trong tổng số {total_chapters} chương.
Phạm vi Batch này: Chương {start_chapter} đến Chương {end_chapter} (Mỗi Arc khoảng {chaps_per_arc} chương).

BẢN ĐỒ THẾ GIỚI QUAN (STORY BIBLE CONTEXT):
- Cốt truyện chính: {premise}
- Địa danh thế giới: {locations_str}
- Các thế lực chính: {factions_str}
- Dàn nhân vật: {chars_str}
- Hệ thống thăng tiến cảnh giới: {ranks_str}
- Quy tắc thế giới: {story_bible.get('rules', [])[:4]}
{prev_summary}
QUY TẮC SÁNG TẠO TỰA ĐỀ VÀ NỘI DUNG (BẮT BUỘC):
1. TỰA ĐỀ ARC (`title`):
   - CẤM TUYỆT ĐỐI đặt tựa đề lặp đi lặp lại hoặc dùng từ chung chung như: "Đấu trường mới", "Đấu trường nguy hiểm", "Đấu trường mới hơn", "Đấu trường phức tạp", "Đấu trường thách thức".
   - Mỗi Tựa đề Arc PHẢI độc nhất, mang tính tiểu thuyết lôi cuốn, kết hợp địa danh/thế lực/cảnh giới/bí mật cụ thể từ bối cảnh (Ví dụ: "Arc {batch_start:02d} — Tân Thủ Làng Sóng Gió", "Arc {batch_start+1:02d} — Khảo Nghiệm Thiên Đô Tông", "Arc {batch_start+2:02d} — Trạm Vũ Trụ Hắc Ám Biến Cố").

2. CHI TIẾT KỊCH BẢN (goal, conflict, major_reveal, character_development):
   - Bám sát tiến trình thăng tiến:
     + Arcs đầu (1-15): Diệp Phàm xuất phát ở vùng tân thủ, gia nhập thế lực khởi đầu, đột phá cấp 1-3.
     + Arcs giữa (16-35): Tranh đoạt tại kinh thành/đại lục, xung đột với thế lực ngầm, đột phá cấp 4-7.
     + Arcs sau (36-50): Tiến ra Thượng giới/Trạm vũ trụ hắc ám, đối đầu boss phản diện cuối, chạm mốc cấp 8-10.
   - CẤM dùng văn mẫu mơ hồ ("gặp nhiều khó khăn", "đối mặt cuộc chiến lớn"). PHẢI nêu rõ xung đột là gì, đối thủ là ai, bí mật tiết lộ là gì!
   - 100% TIẾNG VIỆT MƯỢT MÀ.

3. CẤU TRÚC ĐẦU RA (MẢNG JSON THUẦN TÚY [{batch_count} objects]):
[
  {{
    "arc_num": {batch_start},
    "title": "Arc {batch_start:02d} — [Tựa Đề Độc Nhất Sáng Tạo]",
    "start_chapter": {start_chapter},
    "end_chapter": {start_chapter + chaps_per_arc - 1},
    "goal": "Mục tiêu cụ thể của Diệp Phàm",
    "conflict": "Xung đột cụ thể với nhân vật/thế lực",
    "major_reveal": "Bí mật hoặc phát hiện quan trọng",
    "character_development": "Sự trưởng thành về tâm lý/kỹ năng"
  }}
]"""
