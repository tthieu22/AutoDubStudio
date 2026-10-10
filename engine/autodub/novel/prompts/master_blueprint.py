from typing import Dict, Any


class MasterBlueprintPrompt:
    @staticmethod
    def build_prompt(story_bible: Dict[str, Any], total_chapters: int = 1000, arc_plans: list = None) -> str:
        premise = story_bible.get("premise", "Cốt truyện chính")
        world = story_bible.get("world", {})
        characters = story_bible.get("characters", [])
        rules = story_bible.get("rules", [])
        arcs = arc_plans or story_bible.get("arc_plans", [])

        chars_str = ", ".join([c.get("name", "") for c in characters if isinstance(c, dict) and c.get("name")]) or "Diệp Phàm"

        arcs_summary_str = ""
        if arcs:
            arc_lines = []
            for i, a in enumerate(arcs[:15]):
                num = a.get("arc_num", i + 1)
                start_c = a.get("start_chapter", 1)
                end_c = a.get("end_chapter", 20)
                title = a.get("title", f"Arc {num}")
                goal = a.get("goal", "")
                arc_lines.append(f"  + Arc {num} (Chương {start_c}-{end_c}): {title} | Mục tiêu: {goal}")
            arcs_summary_str = "\n" + "\n".join(arc_lines)
        else:
            arcs_summary_str = "Chưa có danh sách Arc cụ thể"

        return f"""=== VAI TRÒ: MASTER STORY BLUEPRINT ARCHITECT (KIẾN TRÚC SƯ SƯỜN KỊCH BẢN TỔNG THỂ) ===

Nhiệm vụ: Sáng tạo Sườn Kịch Bản Tổng Thể (Master Blueprint Skeleton) cho bộ tiểu thuyết {total_chapters} chương dựa trên Danh Sách Các Arc Kịch Bản đã được lập.
Sườn này đóng vai trò là KIM CHỈ NAM tuyệt đối xuyên suốt 1000 chương, định hướng thống nhất cho toàn bộ các Arc kịch bản, kế hoạch từng chương và văn phong viết phân cảnh.

THÔNG TIN BỐI CẢNH & DANH SÁCH ARCS KỊCH BẢN:
- Tóm tắt tiền đề: {premise}
- Nhân vật chính & dàn cast: {chars_str}
- Thế giới quan: {world}
- Quy tắc thế giới: {rules[:5]}
- Danh sách các Arc Kịch Bản đã lập:{arcs_summary_str}

[OUTPUT CONTRACT - STRICT RAW JSON ONLY]
- Trả về DUY NHẤT 1 JSON Object hợp lệ.
- CẤM kèm bất kỳ lời dẫn, giải thích hay khối markdown codeblock (```json ... ```).
- ĐẦU RA BẮT ĐẦU BẰNG KÝ TỰ '{' VÀ KẾT THÚC BẰNG '}'.

CẤU TRÚC JSON MẪU:
{{
  "overall_arc_summary": "Tóm tắt sườn kịch bản tổng thể từ chương 1 đến chương {total_chapters}, tổng hợp mạch câu chuyện dựa trên chuỗi các Arc kịch bản trên qua 3 giai đoạn đại cục (Khởi đầu xuất sơn, Tranh chấp trung thế giới, Đỉnh phong vũ trụ)",
  "core_conflicts_and_mysteries": [
    "Đại bí ẩn / Mâu thuẫn cốt lõi 1",
    "Đại bí ẩn / Mâu thuẫn cốt lõi 2",
    "Đại bí ẩn / Mâu thuẫn cốt lõi 3"
  ],
  "protagonist_growth_milestones": [
    "Cột mốc 1: Xuất thân tân thủ và phát hiện bí mật đầu tiên",
    "Cột mốc 2: Vươn tầm quy mô thế lực và đột phá cảnh giới trung cấp",
    "Cột mốc 3: Chạm trán boss phản diện chính và làm chủ vận mệnh"
  ],
  "major_climaxes_and_twists": [
    "Twist / Climax 1: Biến cố lớn ở giai đoạn đầu",
    "Twist / Climax 2: Bước ngoặt kịch tính ở giữa bộ truyện",
    "Twist / Climax 3: Đại chiến đỉnh phong kết thúc tác phẩm"
  ],
  "world_timeline_events": [
    "Sự kiện lịch sử / Niên đại 1",
    "Sự kiện lịch sử / Niên đại 2"
  ]
}}
"""

