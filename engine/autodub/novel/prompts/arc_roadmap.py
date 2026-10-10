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

        return f"""=== VAI TRÒ: ARC ROADMAP ARCHITECT (LẬP KẾ HOẠCH LIÊN HOÀN CHO ARC {arc_num}) ===

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
"""

    @staticmethod
    def build_sub_batch_prompt(
        arc: Dict[str, Any],
        story_bible: Dict[str, Any],
        master_blueprint: Dict[str, Any],
        batch_start_chap: int,
        batch_end_chap: int,
        previous_roadmaps: List[Dict[str, Any]] = None
    ) -> str:
        arc_num = arc.get("arc_num", 1)
        arc_title = arc.get("title", f"Arc {arc_num}")
        arc_goal = arc.get("goal", "")
        arc_conflict = arc.get("conflict", "")
        major_reveal = arc.get("major_reveal", "")

        blueprint_summary = master_blueprint.get("overall_arc_summary", "") if isinstance(master_blueprint, dict) else ""
        mysteries = master_blueprint.get("core_conflicts_and_mysteries", []) if isinstance(master_blueprint, dict) else []

        batch_count = batch_end_chap - batch_start_chap + 1

        prev_summary = ""
        if previous_roadmaps and len(previous_roadmaps) > 0:
            prev_lines = []
            for r in previous_roadmaps[-3:]:
                c_num = r.get("chapter_num", "?")
                c_t = r.get("title", "")
                c_g = r.get("goal", "")
                prev_lines.append(f"  - Chương {c_num} ({c_t}): {c_g}")
            if prev_lines:
                prev_summary = "\nCÁC CHƯƠNG ĐÃ TẠO TRƯỚC ĐÓ (Tiếp nối trực tiếp):\n" + "\n".join(prev_lines) + "\n"

        chap_keys_example = []
        for c in range(batch_start_chap, batch_end_chap + 1):
            chap_keys_example.append(f"""  "chapter_{c}": {{
    "chapter_num": {c},
    "title": "Chương {c}: [Tựa đề độc nhất sáng tạo cho Chương {c}]",
    "goal": "[Mục tiêu kịch bản cụ thể của Diệp Phàm trong Chương {c}]",
    "trigger_event": "[Sự kiện kích hoạt diễn biến Chương {c}]",
    "conflict": "[Xung đột / chướng ngại chính trong Chương {c}]",
    "revelation": "[Thông tin mới / kết quả đạt được trong Chương {c}]",
    "transition_hook": "[Móc nối dẫn dắt sang Chương {c + 1}]"
  }}""")

        keys_sample_json = "{\n" + ",\n".join(chap_keys_example) + "\n}"
        req_keys_str = ", ".join([f'"chapter_{c}"' for c in range(batch_start_chap, batch_end_chap + 1)])

        return f"""=== VAI TRÒ: ARC ROADMAP ARCHITECT (LẬP DÀN Ý CHI TIẾT TỪNG CHƯƠNG: Chương {batch_start_chap} đến {batch_end_chap} của Arc {arc_num}) ===

Nhiệm vụ: Hãy sáng tạo Dàn Ý Kịch Bản Chi Tiết Cho TỪNG CHƯƠNG MỘT trong phạm vi từ Chương {batch_start_chap} đến Chương {batch_end_chap} ({batch_count} chương).
Nội dung từng chương PHẢI độc nhất, hấp dẫn, bám sát mục tiêu Arc: "{arc_goal}" và xung đột Arc: "{arc_conflict}".

THÔNG TIN ARC {arc_num}:
- Tựa đề Arc: {arc_title}
- Phạm vi Batch này: Chương {batch_start_chap} đến Chương {batch_end_chap}
- Mục tiêu Arc: {arc_goal}
- Xung đột Arc: {arc_conflict}
- Manh mối / Bí mật lớn: {major_reveal}
- Sườn tổng thể bộ truyện: {blueprint_summary}
- Đại bí ẩn liên quan: {mysteries}
{prev_summary}
QUY TẮC BẮT BUỘC:
1. Trả về JSON Object chứa ĐỦ các key bắt buộc: {req_keys_str}.
2. TUYỆT ĐỐI CẤM dùng văn mẫu chung chung hoặc chép lại tên Arc làm tên chương. Mỗi chương PHẢI có tựa đề và diễn biến riêng!
3. QUAN HỆ NHÂN QUẢ: Chương N kết thúc tạo nguyên nhân cho Chương N+1 bắt đầu. TUYỆT ĐỐI CẤM LẶP LẠI cùng 1 sự kiện ở 2 chương liên tiếp!
4. 100% TIẾNG VIỆT MƯỢT MÀ.

[OUTPUT CONTRACT - STRICT RAW JSON OBJECT ONLY]
- Trả về DUY NHẤT 1 JSON Object với các key bắt buộc: {req_keys_str}.
- CẤM kèm bất kỳ lời dẫn, giải thích hay khối markdown codeblock (```json ... ```).

CẤU TRÚC JSON MẪU:
{keys_sample_json}"""
