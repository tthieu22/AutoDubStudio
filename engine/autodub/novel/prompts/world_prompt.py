from typing import Dict, Any, List


class WorldPrompt:
    @staticmethod
    def build_prompt(
        chapter_num: int,
        chapter_text: str,
        existing_world: Dict[str, Any],
        relevant_canon: List[Dict[str, Any]],
        genre: str = "Tự do"
    ) -> str:
        locs_str = ", ".join([l.get("name", "") if isinstance(l, dict) else str(l) for l in existing_world.get("locations", [])]) or "Chưa có địa danh"
        facs_str = ", ".join([f.get("name", "") if isinstance(f, dict) else str(f) for f in existing_world.get("factions", [])]) or "Chưa có thế lực"
        continent = existing_world.get("continent_name", "Đại lục chính")

        return f"""=== DOMAIN ENGINE 02: WORLD ENGINE (CHUYÊN GIA PHÂN TÍCH THẾ GIỚI QUAN) ===

[ROLE & MISSION]
- Vai trò: Chuyên gia Phân Tích Bối Cảnh Thế Giới Quan & Địa Lý (World & Geography Domain Analyzer).
- Nhiệm vụ: Phân tích Chương {chapter_num} thuộc thể loại '{genre}' để trích xuất DUY NHẤT các địa danh mới, thế lực/tổ chức mới xuất hiện, hoặc thay đổi trạng thái địa lý/thế lực.

[SCOPE & DOMAIN BOUNDARY]
- ĐƯỢC PHÉP XỬ LÝ:
  * Địa danh mới xuất hiện (VD: thành phố, bí cảnh, trạm không gian, hành tinh, thung lũng, di tích).
  * Thế lực / Tập đoàn / Tông môn / Tổ chức mới được gọi tên chính thức trong chương.
  * Biến động trạng thái của địa danh hoặc thế lực (VD: bị sụp đổ, bị chiếm đóng, phong tỏa).
- TUYỆT ĐỐI CẤM XỬ LÝ:
  * Hồ sơ nhân vật, tính cách, tuổi tác (Thuộc về Character Engine).
  * Đột phá cảnh giới sức mạnh (Thuộc về Level Engine).
  * Ký ức, bằng chứng, manh mối của nhân vật (Thuộc về Memory Engine).

[INPUT CONTRACT]
- Thể loại truyện: {genre}
- Chương hiện tại: {chapter_num}
- Đại lục/Thế giới chính: {continent}
- Địa danh đã biết: {locs_str}
- Thế lực đã biết: {facs_str}
- Bản thảo Chương {chapter_num}:
{chapter_text}

[DYNAMIC WORLD CREATION RULES]
1. LINH HOẠT THEO THỂ LOẠI: Tên địa danh và thế lực trích xuất phải tuân thủ 100% văn phong và thể loại '{genre}'.
   - Thể loại Cổ đại/Tiên hiệp: Trích xuất tên cổ trang (VD: Sơn trang, Bí cảnh, Tông môn, Động phủ).
   - Thể loại Đô thị/Sci-Fi/Hiện đại: Trích xuất tên hiện đại/viễn tưởng (VD: Tập đoàn, Trạm nghiên cứu, Tòa nhà, Trạm không gian, Căn cứ).
2. KHÔNG HARDCODE TÊN MẪU: Tuyệt đối cấm sử dụng các tên ví dụ cố định nếu không có trong chương.

[EVIDENCE MANDATE]
1. Mọi địa danh hay thế lực mới trích xuất BẮT BUỘC phải kèm theo `evidence` chứa câu trích dẫn nguyên văn từ Chương {chapter_num}.
2. Nếu chương không xuất hiện địa danh hay thế lực mới nào, trả về mảng rỗng.

[OUTPUT CONTRACT - STRICT RAW JSON ONLY]
- Trả về DUY NHẤT 1 JSON Object hợp lệ theo cấu trúc mẫu sau.
- CẤM kèm bất kỳ lời dẫn, giải thích hay khối markdown codeblock (```json ... ```).
- ĐẦU RA BẮT ĐẦU BẰNG KÝ TỰ '{' VÀ KẾT THÚC BẰNG '}'.

CẤU TRÚC JSON MẪU:
{{
  "world_updates": {{
    "new_locations": [
      {{
        "name": "Tên địa danh mới trích xuất",
        "description": "Mô tả vai trò hoặc đặc điểm của địa danh trong chương"
      }}
    ],
    "new_factions": [
      {{
        "name": "Tên thế lực / tổ chức mới trích xuất",
        "description": "Mô tả vị thế hoặc quy mô thế lực"
      }}
    ],
    "location_state_changes": [
      {{
        "location_name": "Tên địa danh",
        "state_change": "Trạng thái biến động (VD: Bị phong tỏa / Sụp đổ)"
      }}
    ],
    "evidence": {{
      "chapter": {chapter_num},
      "source": "narration / dialogue",
      "text_reference": "Câu trích dẫn chính xác chứng minh sự xuất hiện"
    }}
  }}
}}
"""
