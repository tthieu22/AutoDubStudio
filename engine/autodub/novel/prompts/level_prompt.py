from typing import Dict, Any, List


class LevelPrompt:
    @staticmethod
    def build_prompt(
        chapter_num: int,
        chapter_text: str,
        progression_ranks: List[Any],
        relevant_characters: List[Dict[str, Any]],
        genre: str = "Tự do"
    ) -> str:
        ranks_str = ", ".join([r.get("name", "") if isinstance(r, dict) else str(r) for r in progression_ranks]) or "Hệ thống cấp độ linh hoạt theo câu chuyện"
        chars_str = "\n".join([f"- [{c.get('id')}] {c.get('name')}: Cấp độ/Cảnh giới hiện tại: '{c.get('realm', 'Chưa rõ')}'" for c in relevant_characters]) or "Chưa có nhân vật"

        return f"""=== DOMAIN ENGINE 04: LEVEL ENGINE (CHUYÊN GIA THĂNG CẤP & CẢNH GIỚI) ===

[ROLE & MISSION]
- Vai trò: Chuyên gia Phân Tích Cảnh Giới & Sức Mạnh Nhân Vật (Power Level & Realm Breakthrough Analyzer).
- Nhiệm vụ: Phân tích Chương {chapter_num} thuộc thể loại '{genre}' để xác định DUY NHẤT các sự kiện đột phá cảnh giới, tăng cấp sức mạnh, suy giảm tu vi, hoặc tiến hóa kỹ năng của nhân vật.

[SCOPE & DOMAIN BOUNDARY]
- ĐƯỢC PHÉP XỬ LÝ:
  * Sự kiện đột phá thành công sang cảnh giới/cấp độ mới.
  * Sự kiện cảnh giới bị suy giảm (VD: bị phế tu vi, tụt cấp).
  * Sự kiện lãnh hội kỹ năng/pháp môn mới liên quan đến ngưỡng sức mạnh.
- TUYỆT ĐỐI CẤM XỬ LÝ:
  * Trạng thái tâm lý hay vết thương thông thường (Thuộc về Character Engine).
  * Địa danh, căn cứ, thế lực (Thuộc về World Engine).
  * Tin đồn hay thông tin nhân vật nghe được (Thuộc về Memory Engine).

[INPUT CONTRACT]
- Thể loại truyện: {genre}
- Chương hiện tại: {chapter_num}
- Hệ thống Cấp độ / Cảnh giới của thế giới: {ranks_str}
- Trạng thái Cấp độ hiện tại của nhân vật trong Canon:
{chars_str}
- Bản thảo Chương {chapter_num}:
{chapter_text}

[DYNAMIC PROGRESSION RULES]
1. KHÔNG FIX CỨNG TÊN CẢNH GIỚI: Tên cảnh giới/cấp độ mới trích xuất BẮT BUỘC phải lấy từ bản thảo Chương {chapter_num} và phù hợp văn phong '{genre}'.
   - Thể loại Tiên hiệp/Huyền huyễn: Cảnh giới như Luyện Khí, Trúc Cơ, Kim Đan, Trảm Ngã...
   - Thể loại Sci-Fi/Game/Đô thị: Rank S/A/B/C/D, Kỹ sư Rank 1, Chiến binh Cấp 5, Tiến sĩ Cấp 3...
2. XÁC NHẬN ĐỘT PHÁ THỰC TẾ: Chỉ ghi nhận đột phá nếu bản thảo khẳng định nhân vật ĐÃ ĐỘT PHÁ THÀNH CÔNG trong chương. Không ghi nhận nếu nhân vật mới chỉ đang bế quan hoặc có ý định đột phá.

[EVIDENCE MANDATE]
1. Mọi cập nhật Level BẮT BUỘC phải kèm `evidence` chứa đoạn trích dẫn nguyên văn khẳng định sự đột phá hay thay đổi cấp độ.
2. Nếu trong chương không có nhân vật nào thay đổi cảnh giới/cấp độ sức mạnh, trả về mảng rỗng: "level_updates": [].

[OUTPUT CONTRACT - STRICT RAW JSON ONLY]
- Trả về DUY NHẤT 1 JSON Object hợp lệ theo cấu trúc mẫu sau.
- CẤM kèm bất kỳ lời dẫn, giải thích hay khối markdown codeblock (```json ... ```).
- ĐẦU RA BẮT ĐẦU BẰNG KÝ TỰ '{' VÀ KẾT THÚC BẰNG '}'.

CẤU TRÚC JSON MẪU:
{{
  "level_updates": [
    {{
      "character_id": "Mã ID nhân vật (VD: char_001)",
      "previous_realm": "Cảnh giới / Cấp độ cũ trước chương này",
      "new_realm": "Cảnh giới / Cấp độ mới sau khi đột phá",
      "rank_number": 1,
      "breakthrough_type": "advance / regressed / skill_evolution",
      "evidence": {{
        "chapter": {chapter_num},
        "source": "narration / dialogue",
        "text_reference": "Câu trích dẫn chính xác trong bản thảo chương khẳng định sự đột phá"
      }}
    }}
  ]
}}
"""
