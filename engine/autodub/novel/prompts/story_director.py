from typing import Dict, Any
from autodub.novel.novel_models import StoryIdea


class StoryDirectorPrompt:
    @staticmethod
    def build_prompt(idea: StoryIdea) -> str:
        p_name = idea.protagonist.get("name", "Nhân vật chính") if isinstance(idea.protagonist, dict) else "Nhân vật chính"
        p_bg = idea.protagonist.get("background", "Bối cảnh ban đầu") if isinstance(idea.protagonist, dict) else "Bối cảnh ban đầu"

        return f"""
=== VAI TRÒ: STORY DIRECTOR (GIÁM ĐỐC SÁNG TẠO NỘI DUNG TRUYỆN MỚI) ===
Nhiệm vụ: Dựa trên Ý TƯỞNG CỦA NGHỆ SĨ, hãy sáng tạo BỘ HỒ SƠ THẾ GIỚI & QUY TẮC TRUYỆN (STORY BIBLE) hoàn toàn mới, độc đáo, 100% phù hợp với thể loại và bối cảnh.

THÔNG TIN ĐẦU VÀO TỪ NGƯỜI DÙNG:
- Tên truyện: {idea.title}
- Thể loại: {idea.genre}
- Phong cách: {idea.style}
- Nhân vật chính: {p_name} ({p_bg})
- Yêu cầu đặc biệt: {", ".join(idea.requirements) if idea.requirements else "Sáng tạo độc đáo"}

⚠️ QUY TẮC SÁNG TẠO BẮT BUỘC (CRITICAL MANDATE):
1. Hệ thống tiến trình sức mạnh/cấp độ (`progression_system`) PHẢI được thiết kế CHUẨN THEO THỂ LOẠI '{idea.genre}':
   - Thể loại Tiên Hiệp/Huyền Huyễn: type='cultivation', ranks=['Khởi Đầu', 'Đột Phá', ...]
   - Thể loại Sci-Fi/Vũ Trụ: type='technology', ranks=['Rank D-Kỹ Sư', 'Rank C-Chuyên Viên', ...]
   - Thể loại Game/Dị Năng: type='level', ranks=['F-Rank', 'E-Rank', 'D-Rank', ...]
   - Thể loại Trinh Thám: type='investigation', ranks=['Tập Sự', 'Thám Tử', 'Điều Tra Viên Cao Cấp', ...]
2. CẤM dùng các tên mặc định generic cũ. Hãy sáng tạo tên Tông môn/Thế lực/Tập đoàn/Đại lục/Địa danh HOÀN TOÀN MỚI mang nét đặc trưng của thể loại '{idea.genre}'.
3. Nhân vật chính BẮT BUỘC là: '{p_name}'.

YÊU CẦU ĐẦU RA (Trả về duy nhất 1 JSON Object):
{{
  "premise": "Tóm tắt cốt truyện chủ đạo và bước ngoặt khởi đầu của {p_name}",
  "world": {{
    "continent_name": "Tên thế giới / đại lục / hành tinh chính",
    "factions": ["Thế lực 1", "Thế lực 2"],
    "locations": ["Địa danh khởi đầu", "Bí cảnh/Vùng nguy hiểm"]
  }},
  "progression_system": {{
    "type": "cultivation / technology / level / investigation",
    "ranks": [
      {{"rank": 1, "name": "Cấp độ 1 phù hợp {idea.genre}", "description": "Mô tả sức mạnh cấp 1"}},
      {{"rank": 2, "name": "Cấp độ 2 phù hợp {idea.genre}", "description": "Mô tả sức mạnh cấp 2"}},
      {{"rank": 3, "name": "Cấp độ 3 đỉnh cao", "description": "Mô tả sức mạnh đỉnh cao"}}
    ]
  }},
  "cultivation_system": [
    {{"rank": 1, "name": "Cấp độ 1 phù hợp {idea.genre}", "description": "Mô tả sức mạnh cấp 1"}},
    {{"rank": 2, "name": "Cấp độ 2 phù hợp {idea.genre}", "description": "Mô tả sức mạnh cấp 2"}},
    {{"rank": 3, "name": "Cấp độ 3 đỉnh cao", "description": "Mô tả sức mạnh đỉnh cao"}}
  ],
  "characters": [
    {{
      "id": "char_001",
      "name": "{p_name}",
      "personality": ["Tính cách 1", "Tính cách 2"],
      "goal": "Mục tiêu lớn nhất của {p_name}",
      "realm": "Cấp độ khởi đầu",
      "location": "Vị trí khởi đầu",
      "known_information": ["{p_bg}"],
      "secrets": ["Bí mật lớn nhất / Hệ thống / Kim thủ chỉ"]
    }}
  ],
  "rules": [
    "Cấp độ tuân thủ nghiêm ngặt theo quy tắc thế giới",
    "Nhân vật không thể biết thông tin mà mình chưa từng tiếp xúc"
  ],
  "terminology": {{
    "Thuật ngữ 1": "Mô tả thuật ngữ đặc trưng của thể loại"
  }}
}}
"""
