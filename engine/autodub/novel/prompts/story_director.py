from typing import Dict, Any
from autodub.novel.novel_models import StoryIdea


class StoryDirectorPrompt:
    @staticmethod
    def build_prompt(idea: StoryIdea) -> str:
        return f"""
=== VAI TRÒ: STORY DIRECTOR (GIÁM ĐỐC SÁNG TẠO NỘI DUNG) ===
Nhiệm vụ của bạn là nhận ý tưởng thô và lập BỘ HỒ SƠ THẾ GIỚI & QUY TẮC TRUYỆN (STORY BIBLE) hoàn chỉnh, nhất quán cho một bộ truyện dài {idea.total_chapters} chương.

THÔNG TIN ĐẦU VÀO:
- Tên truyện đề xuất: {idea.title}
- Thể loại: {idea.genre}
- Phong cách văn phong: {idea.style}
- Nhân vật chính: {idea.protagonist}
- Yêu cầu đặc biệt: {", ".join(idea.requirements)}

YÊU CẦU ĐẦU RA (Trả về kết quả dưới dạng duy nhất 1 JSON Object):
{{
  "premise": "Tóm tắt cốt truyện chủ đạo",
  "world": {{
    "continent_name": "Tên đại lục/thế giới",
    "factions": ["Tông môn 1", "Gia tộc 2"],
    "locations": ["Thanh Vân Tông", "Bí Cảnh Tinh Hà"]
  }},
  "cultivation_system": [
    {{"rank": 1, "name": "Luyện Khí", "description": "Tích tụ linh khí vào đan điền"}},
    {{"rank": 2, "name": "Trúc Cơ", "description": "Đúc kết Linh Đài"}},
    {{"rank": 3, "name": "Kim Đan", "description": "Ngưng tụ Kim Đan"}},
    {{"rank": 4, "name": "Nguyên Anh", "description": "Phá Đan thành Anh"}},
    {{"rank": 5, "name": "Hóa Thần", "description": "Thần thức rời khỏi xác"}},
    {{"rank": 6, "name": "Luyện Hư", "description": "Dung hợp hư không"}},
    {{"rank": 7, "name": "Hợp Thể", "description": "Thân tâm hợp nhất"}},
    {{"rank": 8, "name": "Đại Thừa", "description": "Tiên thể viên mãn"}},
    {{"rank": 9, "name": "Độ Kiếp", "description": "Vượt Lôi Kiếp"}},
    {{"rank": 10, "name": "Tiên Nhân", "description": "Tiến vào Tiên Giới"}}
  ],
  "characters": [
    {{
      "id": "char_001",
      "name": "{idea.protagonist.get('name', 'Lâm Phàm')}",
      "personality": ["Thận trọng", "Thông minh", "Quyết đoán"],
      "goal": "Trở thành Tiên Đế",
      "realm": "Luyện Khí",
      "location": "Thanh Vân Tông",
      "known_information": ["Là người hiện đại xuyên không"],
      "secrets": ["Sở hữu Hệ Thống Tiên Nhân"]
    }}
  ],
  "rules": [
    "Cảnh giới là cố định, không được nhảy cảnh giới",
    "Nhân vật không thể biết thông tin mà mình chưa được nghe/thấy"
  ],
  "terminology": {{
    "Linh Khí": "Năng lượng thiên địa",
    "Bí Cảnh": "Không gian độc lập do cao thủ thượng cổ để lại"
  }}
}}
"""
