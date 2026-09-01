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
1. LEAK KÝ ỨC (Knowledge Leak): Nhân vật biết tri thức/bí mật mà họ chưa từng nghe/thấy trong Canon hoặc Chương {chapter_num}.
2. MÂU THUẪN CANON TRỰC TIẾP (Direct Canon Contradiction): Thay đổi trái ngược hoàn toàn với dữ liệu Canon đã xác nhận (VD: Nhân vật đã chết lại xuất hiện nói chuyện, cấp độ bị hạ không lý do, địa danh đổi tên sai hoàn toàn).
3. TRÍCH XUẤT SAI THỰC TẾ (Text Misattribution): Cập nhật Delta trích dẫn đoạn văn bản không hề tồn tại trong Chương {chapter_num}.
4. TỰ Ý BỊA ĐẶT THIẾU CĂN CỨ (Hallucination): Engine tự bịa ra nhân vật/đối tượng không hề có trong câu chuyện.
5. SAI LỆCH VĂN PHONG / THỂ LOẠI: Sử dụng từ ngữ từ thể loại khác không phù hợp với thể loại '{genre}'.

[QUY TẮC PHÂN BIỆT LỖI - BẮT BUỘC]:
1. NẾU NỘI DUNG CHỈ LÀ BỎ SÓT THÔNG TIN HOẶC SUY LUẬN NGỮ CẢNH HỢP LỆ (Ví dụ: Bản thảo chưa đề cập rõ tên thành phố, chưa ghi rõ tên cấp độ 1, hoặc từ ngữ đồng nghĩa) ➔ PHẢI TRẢ VỀ `"status": "PASS"`, `"failures": []`. CẤM BÁO FAIL HOẶC CRITICAL!
2. CHỈ ĐÁNH `"status": "FAIL"` VÀ `"severity": "CRITICAL"` KHI CÓ MÂU THUẪN TRỰC TIẾP VỚI CANON DATABASE HOẶC TRÁI NGƯỢC HOÀN TOÀN VỚI VĂN BẢN (VD: Nhân vật chết xuất hiện, tụt cảnh giới, bí mật bị lọt ra ngoài).

[INPUT CONTRACT]
- Thể loại truyện: {genre}
- Chương hiện tại: {chapter_num}
- Dữ liệu Canon đã lưu giữ:
{canon_str}
- Kết quả đầu ra từ 8 Domain Engine cần thẩm định:
{outputs_str}
- Bản thảo Chương {chapter_num}:
{chapter_text}

[OUTPUT CONTRACT - STRICT RAW JSON ONLY]
- Trả về DUY NHẤT 1 JSON Object hợp lệ theo cấu trúc mẫu sau.
- CẤM kèm bất kỳ lời dẫn, giải thích hay khối markdown codeblock (```json ... ```).
- ĐẦU RA BẮT ĐẦU BẰNG KÝ TỰ '{' VÀ KẾT THÚC BẰNG '}'.

CẤU TRÚC JSON MẪU:
{{
  "status": "PASS / FAIL",
  "failures": [
    {{
      "domain": "Character / World / Memory / Level / Terminology / Event / Relationship / OpenThread",
      "entity": "ID hoặc tên đối tượng bị lỗi",
      "field_name": "Tên trường thông tin bị vi phạm",
      "problem": "Mô tả chi tiết mâu thuẫn Canon hoặc leak thông tin thực sự",
      "evidence": "Câu trích dẫn văn bản chứng minh lỗi (nếu có)",
      "severity": "CRITICAL / MAJOR / WARNING"
    }}
  ]
}}
"""
