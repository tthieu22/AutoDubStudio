from typing import Dict, Any, List


class TerminologyPrompt:
    @staticmethod
    def build_prompt(
        chapter_num: int,
        chapter_text: str,
        known_terms: Dict[str, Any],
        relevant_canon: List[Dict[str, Any]],
        genre: str = "Tự do"
    ) -> str:
        terms_str = ", ".join([f"{k}:{v}" for k, v in list(known_terms.items())[:30]]) or "Chưa có thuật ngữ lưu trữ"

        return f"""=== DOMAIN ENGINE 05: TERMINOLOGY ENGINE (CHUYÊN GIA THUẬT NGỮ CHUẨN CANON) ===

[ROLE & MISSION]
- Vai trò: Chuyên gia Bảo Tồn & Quản Lý Thuật Ngữ Canon (Canonical Terminology Engine).
- Nhiệm vụ: Phân tích Chương {chapter_num} thuộc thể loại '{genre}' để trích xuất các thuật ngữ độc đáo MỚI (tên công pháp, tên vật phẩm, danh xưng danh dự, danh từ riêng chuyên môn) và bảo đảm tính đồng nhất thuật ngữ xuyên suốt.

[SCOPE & DOMAIN BOUNDARY]
- ĐƯỢC PHÉP XỬ LÝ:
  * Tên danh từ riêng độc đáo lần đầu xuất hiện (VD: tên công pháp, bảo vật, loại nhiên liệu, công nghệ đặc thù, dị vật).
  * Định nghĩa ngắn gọn của thuật ngữ dựa trên ngữ cảnh chương.
- TUYỆT ĐỐI CẤM XỬ LÝ:
  * Tên nhân vật (Thuộc về Character Engine).
  * Tên địa danh/thế lực (Thuộc về World Engine).
  * Diễn biến sự kiện lịch sử (Thuộc về Event Engine).

[INPUT CONTRACT]
- Thể loại truyện: {genre}
- Chương hiện tại: {chapter_num}
- Danh sách Thuật ngữ Canon đã lưu giữ: {terms_str}
- Bản thảo Chương {chapter_num}:
{chapter_text}

[DYNAMIC TERMINOLOGY RULES]
1. KHÔNG LẶP THUẬT NGỮ THÔNG THƯỜNG: Không trích xuất các từ ngữ tiếng Việt thông dụng (VD: 'Thanh kiếm', 'Con sông', 'Chiếc xe'). Chỉ trích xuất thuật ngữ mang tính danh từ riêng hoặc từ chuyên môn độc đáo của tác phẩm.
2. PHÙ HỢP VĂN PHONG VÀ THỂ LOẠI: Thuật ngữ phải tôn trọng tuyệt đối thể loại '{genre}'.
3. ĐỒNG NHẤT KHÔNG THAY ĐỔI: Nếu thuật ngữ đã có trong Canon (VD: 'Hồng Mông Khí' hoặc 'Động Cơ Siêu Tốc'), giữ nguyên 100% không đổi tên.

[EVIDENCE MANDATE]
1. Mọi thuật ngữ mới trích xuất BẮT BUỘC phải kèm `evidence` trích dẫn câu văn lần đầu thuật ngữ xuất hiện.
2. Nếu chương không xuất hiện thuật ngữ chuyên môn mới nào, trả về mảng rỗng: "terminology_updates": [].

[OUTPUT CONTRACT (JSON SCHEMA)]
Trả về DUY NHẤT một JSON Object hợp lệ:
{{
  "terminology_updates": [
    {{
      "term_key": "Thuật ngữ tiếng Việt chính xác (VD: Hồng Mông Khí / Động Cơ Siêu Tốc)",
      "canonical_name": "Tên chuẩn hóa",
      "category": "Item / Spell / Technology / Rule / Resource",
      "definition": "Định nghĩa hoặc công dụng ngắn gọn của thuật ngữ",
      "evidence": {{
        "chapter": {chapter_num},
        "source": "narration / dialogue",
        "text_reference": "Câu trích dẫn chính xác trong bản thảo chương xuất hiện thuật ngữ"
      }}
    }}
  ]
}}
"""
