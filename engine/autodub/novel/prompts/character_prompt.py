from typing import Dict, Any, List


class CharacterPrompt:
    @staticmethod
    def build_prompt(
        chapter_num: int,
        chapter_text: str,
        relevant_characters: List[Dict[str, Any]],
        relevant_canon: List[Dict[str, Any]],
        genre: str = "Tự do"
    ) -> str:
        chars_str = "\n".join([f"- ID [{c.get('id')}]: {c.get('name')} | Cảnh giới: {c.get('realm', 'Chưa rõ')} | Giới tính: {c.get('gender', 'Chưa rõ')}" for c in relevant_characters]) or "Chưa có nhân vật trong Canon"
        canon_str = "\n".join([f"- [{c.get('category', 'Lore')}] {c.get('fact_text')}" for c in relevant_canon]) or "Không có dữ liệu Canon cũ"

        return f"""=== DOMAIN ENGINE 01: CHARACTER ENGINE (CHUYÊN GIA PHÂN TÍCH NHÂN VẬT) ===

[ROLE & MISSION]
- Vai trò: Chuyên gia Phân Tích & Theo Dõi Nhân Vật Chuyên Sâu (Deterministic Character Domain Analyzer).
- Nhiệm vụ: Phân tích kỹ lưỡng bản thảo Chương {chapter_num} thuộc thể loại '{genre}' để trích xuất DUY NHẤT các thay đổi Delta thực tế về danh tính, thuộc tính, trạng thái sinh tồn và hành trạng của nhân vật.

[SCOPE & DOMAIN BOUNDARY]
- ĐƯỢC PHÉP XỬ LÝ:
  * Trạng thái nhân vật thay đổi trong chương (VD: bị thương, hồi phục, nhập hội, tách đoàn, bất tỉnh, biến mất).
  * Thuộc tính mới của nhân vật được xác nhận rõ trong chương (VD: danh hiệu mới, chức vụ mới).
  * Các biến động hành vi và tâm lý gắn liền với bằng chứng trực tiếp.
- TUYỆT ĐỐI CẤM XỬ LÝ:
  * Cảnh giới / Cấp độ sức mạnh (Thuộc về Level Engine).
  * Vùng đất / Địa danh / Thế lực (Thuộc về World Engine).
  * Tri thức / Ký ức / Lời đồn (Thuộc về Memory Engine).
  * Thuật ngữ riêng / Tên pháp bảo / Công pháp (Thuộc về Terminology Engine).

[INPUT CONTRACT]
- Thể loại truyện: {genre}
- Chương hiện tại: {chapter_num}
- Danh sách Nhân vật Canon hiện có:
{chars_str}
- Dữ liệu Canon liên quan:
{canon_str}
- Bản thảo Chương {chapter_num}:
{chapter_text}

[CANON & ID CONSISTENCY RULES]
1. NẾU NHÂN VẬT ĐÃ TỒN TẠI TRONG CANON: BẮT BUỘC tái sử dụng exact character_id (VD: char_001). Tuyệt đối CẤM tự bịa ID mới (VD: character_99) cho nhân vật đã có.
2. NẾU XUẤT HIỆN NHÂN VẬT MỚI RÕ RÀNG: Chỉ ghi nhận nếu nhân vật đó đóng vai trò thoại hoặc có tên tuổi cụ thể trong chương.

[EVIDENCE MANDATE]
1. Mọi thay đổi Delta BẮT BUỘC phải đi kèm đối tượng `evidence` chứa câu trích dẫn nguyên văn (`text_reference`) từ bản thảo Chương {chapter_num}.
2. Nếu không có trích dẫn văn bản chứng minh, KHÔNG ĐƯỢC CẬP NHẬT.

[NEGATIVE RULES & NO-INVENTION POLICY]
- KHÔNG tự bịa suy đoán tính cách hay trạng thái nếu văn bản không đề cập.
- KHÔNG dùng từ giữ chỗ generic (VD: 'Thay đổi 1', 'Trạng thái A').
- KHÔNG tự bịa ra cái chết hay sự biến mất của nhân vật trừ khi văn bản khẳng định rõ.
- Nếu nhân vật không có biến động trạng thái nào trong chương, trả về mảng rỗng: "character_updates": [].

[OUTPUT CONTRACT (JSON SCHEMA)]
Trả về DUY NHẤT một JSON Object hợp lệ (không kèm lời dẫn lời giải thích):
{{
  "character_updates": [
    {{
      "character_id": "Mã ID nhân vật (VD: char_001)",
      "status_change": "Mô tả trạng thái biến động ngắn gọn sắc sảo",
      "new_attributes": {{
        "title": "Danh hiệu mới (nếu có)",
        "role": "Chức vụ mới (nếu có)"
      }},
      "state_changes": [
        "Mô tả sự thay đổi cụ thể 1"
      ],
      "evidence": {{
        "chapter": {chapter_num},
        "source": "dialogue / narration / action",
        "text_reference": "Câu trích dẫn chính xác từ bản thảo chương"
      }}
    }}
  ]
}}
"""
