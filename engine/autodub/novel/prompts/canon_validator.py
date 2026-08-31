from typing import Dict, Any, List
import json


class CanonValidatorPrompt:
    @staticmethod
    def build_prompt(
        chapter_num: int,
        chapter_text: str,
        engine_outputs: Dict[str, Any],
        relevant_canon: List[Dict[str, Any]],
        genre: str = "Tự do"
    ) -> str:
        canon_str = "\n".join([f"- [{c.get('category', 'Canon')}] {c.get('fact_text')}" for c in relevant_canon]) or "Chưa có dữ liệu Canon cũ"
        outputs_str = json.dumps(engine_outputs, ensure_ascii=False, indent=2)

        return f"""=== DOMAIN ENGINE 09: CROSS-DOMAIN CANON VALIDATOR (THẨM ĐỊNH VIÊN ĐỘC LẬP) ===

[ROLE & MISSION]
- Vai trò: Thẩm định viên Độc Lập Chéo Domain & Bảo Vệ Canon (Cross-Domain Strict Canon Validator & Gatekeeper).
- Nhiệm vụ: Phân tích và thẩm định toàn bộ kết quả trích xuất từ 8 Domain Engine (Character, World, Memory, Level, Terminology, Event, Relationship, Open Thread) thuộc thể loại '{genre}', đối chiếu trực tiếp với bản thảo Chương {chapter_num} và Dữ liệu Canon Database.

[CRITICAL VALIDATION CHECKLIST]
Kiểm tra nghiêm ngặt 5 nguy cơ lỗi sau:
1. LEAK KÝ ỨC (Knowledge Leak): Nhân vật biết tri thức mà họ chưa từng nghe/thấy trong Canon hoặc Chương {chapter_num}.
2. MÂU THUẪN CANON (Canon Contradiction): Thay đổi trái ngược hoàn toàn với dữ liệu Canon đã xác nhận (VD: Nhân vật đã chết lại xuất hiện, cấp độ bị hạ không lý do, địa danh đổi tên tự do).
3. TRÍCH XUẤT SAI THỰC TẾ (Text Misattribution): Cập nhật Delta trích dẫn đoạn văn bản không hề tồn tại trong Chương {chapter_num}.
4. TỰ Ý BỊA ĐẶT (Hallucination): Engine tự bịa ra nhân vật, cấp độ, hoặc sự kiện không có bất kỳ chứng cứ nào trong chương.
5. SAI LỆCH VĂN PHONG / THỂ LOẠI: Sử dụng từ ngữ từ thể loại khác không phù hợp với thể loại '{genre}'.

[INPUT CONTRACT]
- Thể loại truyện: {genre}
- Chương hiện tại: {chapter_num}
- Dữ liệu Canon đã lưu giữ:
{canon_str}
- Kết quả đầu ra từ 8 Domain Engine cần thẩm định:
{outputs_str}
- Bản thảo Chương {chapter_num}:
{chapter_text}

[FAIL-CLOSED MANDATE]
1. BẠN LÀ NGUYÊN TẮC PHÒNG THỦ CUỐI CÙNG: Không được nể nang hay bỏ qua lỗi.
2. KHÔNG ĐƯỢC TỰ SỬA LỖI: Bạn KHÔNG được tự ý chỉnh sửa dữ liệu sai của 8 Engine.
3. CHỈ ĐƯỢC ĐÁNH GIÁ "PASS" HOẶC "FAIL":
   - NẾU TẤT CẢ 8 ENGINE CHÍNH XÁC & CÓ EVIDENCE HỢP LỆ -> Trả về `"status": "PASS"`, `"failures": []`.
   - NẾU CÓ BẤT KỲ LỖI NÀO TRONG 5 NGUY CƠ TRÊN -> Trả về `"status": "FAIL"` và liệt kê tất cả các lỗi trong mảng `"failures"`.

[OUTPUT CONTRACT (JSON SCHEMA)]
Trả về DUY NHẤT một JSON Object hợp lệ:
{{
  "status": "PASS / FAIL",
  "failures": [
    {{
      "domain": "Character / World / Memory / Level / Terminology / Event / Relationship / OpenThread",
      "entity": "ID hoặc tên đối tượng bị lỗi",
      "field_name": "Tên trường thông tin bị vi phạm",
      "problem": "Mô tả chi tiết nguyên nhân vi phạm mâu thuẫn Canon hoặc leak thông tin",
      "evidence": "Câu trích dẫn văn bản chứng minh lỗi (nếu có)",
      "severity": "CRITICAL / MAJOR"
    }}
  ]
}}
"""
