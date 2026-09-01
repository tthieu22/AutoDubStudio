from typing import Dict, Any, List


class RelationshipPrompt:
    @staticmethod
    def build_prompt(
        chapter_num: int,
        chapter_text: str,
        relevant_characters: List[Dict[str, Any]],
        existing_relationships: List[Dict[str, Any]],
        genre: str = "Tự do"
    ) -> str:
        chars_str = ", ".join([f"{c.get('id')}:{c.get('name')}" for c in relevant_characters]) or "Chưa có nhân vật"
        rels_str = "\n".join([f"- {r.get('source_entity')} -> {r.get('target_entity')}: {r.get('relationship_type')} ({r.get('status')})" for r in existing_relationships]) or "Chưa có mối quan hệ cũ"

        return f"""=== DOMAIN ENGINE 07: RELATIONSHIP ENGINE (CHUYÊN GIA MỐI QUAN HỆ THỰC THỂ) ===

[ROLE & MISSION]
- Vai trò: Chuyên gia Phân Tích Mối Quan Hệ & Liên Minh (Entity Relationship & Alliance Analyzer).
- Nhiệm vụ: Phân tích Chương {chapter_num} thuộc thể loại '{genre}' để xác định DUY NHẤT các thiết lập mới hoặc biến động trong mối quan hệ giữa các nhân vật/thực thể.

[RELATIONSHIP TYPES & STATUSES]
- Loại quan hệ (`relationship_type`):
  * ALLIANCE (Đồng minh / Hợp tác)
  * ENMITY (Thù địch / Kẻ thù)
  * MENTORSHIP (Sư đồ / Thầy trò / Cấp trên - Cấp dưới)
  * ROMANCE (Tình cảm / Bán duyên)
  * FAMILY (Gia tộc / Dòng họ)
  * RIVALRY (Đối thủ cạnh tranh)
- Trạng thái quan hệ (`status`):
  * ESTABLISHED (Mới thiết lập)
  * STRENGTHENED (Được thắt chặt)
  * WEAKENED (Biết rạn nứt)
  * BROKEN (Đã phản bội / Tan vỡ)

[INPUT CONTRACT]
- Thể loại truyện: {genre}
- Chương hiện tại: {chapter_num}
- Danh sách Nhân vật: {chars_str}
- Quan hệ hiện có trong Canon:
{rels_str}
- Bản thảo Chương {chapter_num}:
{chapter_text}

[DYNAMIC RELATIONSHIP RULES]
1. TÁI SỬ DỤNG ID NHÂN VẬT: `source_entity` và `target_entity` BẮT BUỘC phải dùng `character_id` chính xác (VD: char_001).
2. XÁC NHẬN BẰNG HÀNH ĐỘNG: Quan hệ thay đổi phải dựa trên sự kiện/hành động/lời nói thực tế trong chương (VD: Thề nguyện làm bạn -> ALLIANCE; Đâm sau lưng -> BROKEN).

[EVIDENCE MANDATE]
1. Mọi cập nhật mối quan hệ BẮT BUỘC phải kèm `evidence` trích dẫn chính xác hành động hoặc lời nói.
2. Nếu không có mối quan hệ nào biến động trong chương, trả về mảng rỗng: "relationship_updates": [].

[OUTPUT CONTRACT - STRICT RAW JSON ONLY]
- Trả về DUY NHẤT 1 JSON Object hợp lệ theo cấu trúc mẫu sau.
- CẤM kèm bất kỳ lời dẫn, giải thích hay khối markdown codeblock (```json ... ```).
- ĐẦU RA BẮT ĐẦU BẰNG KÝ TỰ '{' VÀ KẾT THÚC BẰNG '}'.

CẤU TRÚC JSON MẪU:
{{
  "relationship_updates": [
    {{
      "source_entity": "Mã ID nhân vật 1 (VD: char_001)",
      "target_entity": "Mã ID nhân vật 2 (VD: char_002)",
      "relationship_type": "ALLIANCE / ENMITY / MENTORSHIP / ROMANCE / FAMILY / RIVALRY",
      "status": "ESTABLISHED / STRENGTHENED / WEAKENED / BROKEN",
      "description": "Mô tả ngắn về sự biến chuyển mối quan hệ trong chương",
      "evidence": {{
        "chapter": {chapter_num},
        "source": "dialogue / action",
        "text_reference": "Câu trích dẫn chính xác chứng minh biến động mối quan hệ"
      }}
    }}
  ]
}}
"""
