from typing import Dict, Any, List


class ArcRoadmapPrompt:
    @staticmethod
    def build_prompt(
        arc: Dict[str, Any],
        story_bible: Dict[str, Any],
        master_blueprint: Dict[str, Any],
        previous_roadmaps_summary: str = ""
    ) -> str:
        arc_num = arc.get("arc_num", 1)
        arc_title = arc.get("title", f"Arc {arc_num}")
        start_chap = arc.get("start_chapter", 1)
        end_chap = arc.get("end_chapter", 20)
        arc_goal = arc.get("goal", "")
        arc_conflict = arc.get("conflict", "")
        major_reveal = arc.get("major_reveal", "")

        blueprint_summary = master_blueprint.get("overall_arc_summary", "") if isinstance(master_blueprint, dict) else ""
        mysteries = master_blueprint.get("core_conflicts_and_mysteries", []) if isinstance(master_blueprint, dict) else []

        return f"""=== VAI TRÒ: ARC ROADMAP ARCHITECT (LẬP KẾ HOẠCH LIÊN HOÀN 20 CHƯƠNG CHO ARC {arc_num}) ===

Nhiệm vụ: Hãy tạo Dàn Ý Kịch Bản Chi Tiết Cho Cả Arc (từ Chương {start_chap} đến Chương {end_chap}).
Dàn ý này PHẢI nối tiếp nhau theo chuỗi nhân quả (Causal Chain continuous plot) nhằm TRIỆT TIÊU NGUY CƠ LẶP LẠI NỘI DUNG GIỮA CÁC CHƯƠNG.

THÔNG TIN ARC {arc_num}:
- Tựa đề Arc: {arc_title}
- Chương: từ {start_chap} đến {end_chap}
- Mục tiêu Arc: {arc_goal}
- Xung đột Arc: {arc_conflict}
- Manh mối / Bí mật lớn: {major_reveal}
- Sườn tổng thể bộ truyện: {blueprint_summary}
- Đại bí ẩn liên quan: {mysteries}
{previous_roadmaps_summary}

QUY TẮC BẮT BUỘC:
1. Tạo lập dàn ý kịch bản cho ĐỦ {end_chap - start_chap + 1} chương (Chương {start_chap} -> Chương {end_chap}).
2. MỖI CHƯƠNG BẮT BUỘC CÓ:
   - `chapter_num`: Số chương
   - `title`: Tựa đề chương độc nhất
   - `goal`: Mục tiêu kịch bản cụ thể của chương
   - `trigger_event`: Sự kiện khởi đầu / Động lực kích hoạt
   - `conflict`: Xung đột / Chướng ngại chính
   - `revelation`: Thông tin mới / Manh mối / Kết quả đạt được
   - `transition_hook`: Dẫn dắt sang chương tiếp theo
3. QUAN HỆ NHÂN QUẢ: Chương N kết thúc tạo nguyên nhân cho Chương N+1 bắt đầu. TUYỆT ĐỐI CẤM LẶP LẠI cùng 1 sự kiện hay phát hiện ở 2 chương liên tiếp!
4. 100% TIẾNG VIỆT MƯỢT MÀ, KHÔNG VIẾT CHUNG CHUNG MƠ HỒ.

[OUTPUT CONTRACT - STRICT RAW JSON ONLY]
- Trả về DUY NHẤT 1 Mảng JSON (JSON Array) hợp lệ.
- CẤM kèm bất kỳ lời dẫn, giải thích hay khối markdown codeblock (```json ... ```).
- ĐẦU RA BẮT ĐẦU BẰNG KÝ TỰ '[' VÀ KẾT THÚC BẰNG ']'.

CẤU TRÚC JSON MẪU:
[
  {{
    "chapter_num": {start_chap},
    "title": "Chương {start_chap}: [Tựa Đề]",
    "goal": "Diệp Phàm bước ra khỏi phòng, thu thập tin tức tại sảnh...",
    "trigger_event": "Nhận thấy bầu không khí bất thường ở thành phố...",
    "conflict": "Chạm trán đệ tử thế lực đối lập",
    "revelation": "Tiết lộ tung tích cổ thư",
    "transition_hook": "Quyết định đêm nay thâm nhập tàng kinh các"
  }}
]
"""
