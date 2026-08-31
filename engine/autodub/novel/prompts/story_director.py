from typing import Dict, Any
from autodub.novel.novel_models import StoryIdea


class StoryDirectorPrompt:
    @staticmethod
    def build_prompt(idea: StoryIdea) -> str:
        """Tổng hợp prompt khởi tạo Bối cảnh thế giới & Hồ sơ truyện."""
        p_name = idea.protagonist.get("name", "Nhân vật chính") if isinstance(idea.protagonist, dict) else "Nhân vật chính"
        p_bg = idea.protagonist.get("background", "Bối cảnh ban đầu") if isinstance(idea.protagonist, dict) else "Bối cảnh ban đầu"

        return f"""=== VAI TRÒ: STORY DIRECTOR (GIÁM ĐỐC SÁNG TẠO NỘI DUNG TRUYỆN MỚI) ===
Nhiệm vụ: Dựa trên Ý TƯỞNG CỦA NGHỆ SĨ, hãy sáng tạo BỘ HỒ SƠ THẾ GIỚI & QUY TẮC TRUYỆN (STORY BIBLE) hoàn toàn mới, độc đáo, 100% phù hợp với thể loại và bối cảnh.

THÔNG TIN ĐẦU VÀO TỪ NGƯỜI DÙNG:
- Tên truyện: {idea.title}
- Thể loại: {idea.genre}
- Phong cách: {idea.style}
- Nhân vật chính: {p_name} ({p_bg})
- Yêu cầu đặc biệt: {", ".join(idea.requirements) if idea.requirements else "Sáng tạo độc đáo"}

QUY TẮC SÁNG TẠO BẮT BUỘC:
1. Hệ thống tiến trình sức mạnh/cấp độ (`progression_system`) PHẢI được thiết kế CHUẨN THEO THỂ LOẠI '{idea.genre}'.
2. CẤM dùng các tên mặc định generic cũ. Hãy sáng tạo tên Tông môn/Thế lực/Tập đoàn/Đại lục/Địa danh HOÀN TOÀN MỚI mang nét đặc trưng của thể loại '{idea.genre}'.
3. Nhân vật chính BẮT BUỘC là: '{p_name}'.
4. BẮT BUỘC SÁNG TẠO DÀN NHÂN VẬT ĐẦY ĐỦ THẾ GIỚI QUAN (Ít nhất 4 - 6 nhân vật bao gồm CẢ NAM VÀ NỮ). CẤM tạo dàn nhân vật 100% Nam.
5. TÊN CÁC NHÂN VẬT PHẢI PHỔ THÔNG, TỰ NHIÊN, CÓ ĐỘ NHẬN DIỆN CAO (Ví dụ: Nguyệt Nhi, Vân Tiêu, Tiêu Viêm, Minh Quân, Alex Vance...).
6. TOÀN BỘ NỘI DUNG VĂN BẢN TRONG ĐẦU RA JSON BẮT BUỘC PHẢI VIẾT 100% BẰNG TIẾNG VIỆT MƯỢT MÀ, TỰ NHIÊN. CẤM TRẢ VỀ TIẾNG ANH/TRUNG.
7. CẤM BẢO LƯU CÁC TỪ MẪU GENERIC NHƯ 'Tính cách 1', 'Mô tả 1'. Mọi mô tả PHẢI ĐƯỢC VIẾT CỤ THỂ, SẮC SẢO.
8. BẮT BUỘC SÁNG TẠO THẾ GIỚI RỘNG LỚN (Mục factions: 4-6 thế lực; Mục locations: 5-8 địa danh).

YÊU CẦU ĐẦU RA (Trả về duy nhất 1 JSON Object):
{{
  "premise": "Tóm tắt cốt truyện chủ đạo và bước ngoặt khởi đầu của {p_name}",
  "world": {{
    "continent_name": "Tên thế giới / đại lục / hành tinh chính",
    "factions": [
      "Thế lực khởi đầu / Tông môn chính",
      "Liên minh thương hội / Chợ giao dịch",
      "Đại tập đoàn / Hoàng gia cai trị",
      "Tổ chức phản diện / Ngầm",
      "Thế lực ẩn thế / Cổ xưa"
    ],
    "locations": [
      "Vùng đất khởi đầu (Làng/Tân thủ/Trạm vũ trụ)",
      "Thành phố / Kinh thành trung tâm",
      "Trung tâm giao dịch / Chợ đấu giá",
      "Bí cảnh / Vùng nguy hiểm thử thách",
      "Vùng đất cấm / Di tích cổ xưa",
      "Tổng bộ thế lực đối lập"
    ]
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
      "gender": "Nam",
      "personality": ["Điềm tĩnh", "Quyết đoán", "Thông minh"],
      "goal": "Mục tiêu lớn nhất của {p_name}",
      "realm": "Cấp độ khởi đầu",
      "location": "Vị trí khởi đầu",
      "known_information": ["{p_bg}"],
      "secrets": ["Bí mật lớn nhất / Hệ thống / Kim thủ chỉ"]
    }},
    {{
      "id": "char_002",
      "name": "Nguyệt Nhi",
      "gender": "Nữ",
      "personality": ["Sắc sảo", "Thông minh", "Trung thành"],
      "goal": "Sát cánh và hỗ trợ {p_name}",
      "realm": "Cấp độ khởi đầu",
      "location": "Vị trí khởi đầu",
      "known_information": ["Bối cảnh thân thế nữ đồng đội"],
      "secrets": ["Bí mật gia thế / Manh mối cổ xưa"]
    }},
    {{
      "id": "char_003",
      "name": "Lão Trâu",
      "gender": "Nam",
      "personality": ["Uy nghiêm", "Sâu sắc"],
      "goal": "Hướng dẫn và bảo vệ thế hệ trẻ",
      "realm": "Cấp độ cao",
      "location": "Tổ chức / Tông môn",
      "known_information": ["Bí mật lịch sử thế giới"],
      "secrets": ["Vết thương cũ / Âm mưu quá khứ"]
    }},
    {{
      "id": "char_004",
      "name": "Phương Thảo",
      "gender": "Nữ",
      "personality": ["Kiêu ngạo", "Sắc bén"],
      "goal": "Tranh đoạt tài nguyên / Thách thức {p_name}",
      "realm": "Cấp độ nhỉnh hơn char_001",
      "location": "Thế lực đối lập",
      "known_information": ["Kế hoạch chèn ép"],
      "secrets": ["Hậu thuẫn đằng sau"]
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

    @staticmethod
    def build_world_prompt(idea: StoryIdea) -> str:
        """Step 1A: Prompt dành riêng cho Bối cảnh thế giới."""
        return StoryDirectorPrompt.build_prompt(idea)

    @staticmethod
    def build_progression_prompt(idea: StoryIdea, premise: str) -> str:
        """Step 1B: Sáng tạo Hệ thống Cấp độ / Cảnh giới tiến trình sức mạnh độc lập."""
        return f"""=== STEP 1B: SÁNG TẠO HỆ THỐNG CẤP ĐỘ SỨC MẠNH ===
Nhiệm vụ: Sáng tạo hệ thống tiến trình sức mạnh (5 - 8 cấp độ) CHUẨN XÁC THEO THỂ LOẠI '{idea.genre}'.

BỐI CẢNH TIỀN ĐỀ: {premise}

QUY TẮC BẮT BUỘC:
- Thể loại Tiên Hiệp/Huyền Huyễn: type='cultivation', ranks chuẩn cổ trang.
- Thể loại Sci-Fi/Vũ Trụ: type='technology', ranks chuẩn khoa học kỹ thuật.
- Thể loại Game/Dị Năng: type='level', ranks chuẩn F-Rank đến SSS-Rank.
- Thể loại Trinh Thám: type='investigation', ranks chuẩn cấp bậc điều tra.
- TOÀN BỘ NỘI DUNG VIẾT BẰNG TIẾNG VIỆT 100%.

ĐẦU RA PHẢI LÀ HOÀN TOÀN TRẢ VỀ 1 JSON OBJECT DUY NHẤT:
{{
  "progression_system": {{
    "type": "cultivation / technology / level / investigation",
    "ranks": [
      {{"rank": 1, "name": "Cấp độ 1 Khởi Đầu", "description": "Mô tả sức mạnh cấp 1"}},
      {{"rank": 2, "name": "Cấp độ 2 Tiến Bổn", "description": "Mô tả sức mạnh cấp 2"}},
      {{"rank": 3, "name": "Cấp độ 3 Đột Phá", "description": "Mô tả sức mạnh cấp 3"}},
      {{"rank": 4, "name": "Cấp độ 4 Chuyên Viên", "description": "Mô tả sức mạnh cấp 4"}},
      {{"rank": 5, "name": "Cấp độ 5 Đỉnh Phong", "description": "Mô tả sức mạnh cấp 5"}}
    ]
  }},
  "cultivation_system": [
    {{"rank": 1, "name": "Cấp độ 1 Khởi Đầu", "description": "Mô tả sức mạnh cấp 1"}},
    {{"rank": 2, "name": "Cấp độ 2 Tiến Bổn", "description": "Mô tả sức mạnh cấp 2"}},
    {{"rank": 3, "name": "Cấp độ 3 Đột Phá", "description": "Mô tả sức mạnh cấp 3"}},
    {{"rank": 4, "name": "Cấp độ 4 Chuyên Viên", "description": "Mô tả sức mạnh cấp 4"}},
    {{"rank": 5, "name": "Cấp độ 5 Đỉnh Phong", "description": "Mô tả sức mạnh cấp 5"}}
  ]
}}
"""

    @staticmethod
    def build_cast_prompt(idea: StoryIdea, world_info: Dict[str, Any]) -> str:
        """Step 1C: Sáng tạo Dàn nhân vật nòng cốt (Đầy đủ Nam & Nữ) độc lập."""
        p_name = idea.protagonist.get("name", "Nhân vật chính") if isinstance(idea.protagonist, dict) else "Nhân vật chính"
        p_bg = idea.protagonist.get("background", "Bối cảnh ban đầu") if isinstance(idea.protagonist, dict) else "Bối cảnh ban đầu"
        premise = world_info.get("premise", "Cốt truyện chính")
        continent = world_info.get("world", {}).get("continent_name", "Thế giới")

        return f"""=== STEP 1C: SÁNG TẠO DÀN NHÂN VẬT THẾ GIỚI QUAN ===
Nhiệm vụ: Dựa trên Tiền đề '{premise}' và Đại lục '{continent}', hãy sáng tạo DÀN NHÂN VẬT NÒNG CỐT (4 - 6 nhân vật bao gồm CẢ NAM VÀ NỮ).

QUY TẮC BẮT BUỘC:
1. BẮT BUỘC CÓ CẢ NAM VÀ NỮ (Ít nhất 2 nhân vật Nữ như Nữ chính/Bạn đồng hành nữ, Nữ đối thủ, Nữ sư phụ).
2. Tên nhân vật phải tự nhiên, hợp thể loại '{idea.genre}'. CẤM dùng các từ giữ chỗ 'Tính cách 1', 'Địa danh 1'.
3. TOÀN BỘ VIẾT BẰNG TIẾNG VIỆT 100%.

ĐẦU RA PHẢI LÀ MẢNG JSON CÁC NHÂN VẬT:
[
  {{
    "id": "char_001",
    "name": "{p_name}",
    "gender": "Nam",
    "personality": ["Điềm tĩnh", "Thông minh", "Quyết đoán"],
    "goal": "Mục tiêu lớn nhất",
    "realm": "Cấp độ 1 Khởi Đầu",
    "location": "Vị trí khởi đầu",
    "known_information": ["{p_bg}"],
    "secrets": ["Kim thủ chỉ / Bí mật lớn"]
  }},
  {{
    "id": "char_002",
    "name": "Nguyệt Nhi",
    "gender": "Nữ",
    "personality": ["Sắc sảo", "Thông minh", "Trung thành"],
    "goal": "Sát cánh hỗ trợ {p_name}",
    "realm": "Cấp độ 1 Khởi Đầu",
    "location": "Vị trí khởi đầu",
    "known_information": ["Gia thế đồng đội"],
    "secrets": ["Bí mật gia thế / Manh mối cổ"]
  }},
  {{
    "id": "char_003",
    "name": "Lão Trâu",
    "gender": "Nam",
    "personality": ["Uy nghiêm", "Sâu sắc"],
    "goal": "Dẫn đường thế hệ trẻ",
    "realm": "Cấp độ cao",
    "location": "Tổng bộ thế lực",
    "known_information": ["Lịch sử thế giới"],
    "secrets": ["Âm mưu quá khứ"]
  }},
  {{
    "id": "char_004",
    "name": "Phương Thảo",
    "gender": "Nữ",
    "personality": ["Kiêu ngạo", "Sắc bén"],
    "goal": "Tranh đoạt tài nguyên",
    "realm": "Cấp độ 2 Tiến Bổn",
    "location": "Thế lực đối lập",
    "known_information": ["Kế hoạch chèn ép"],
    "secrets": ["Hậu thuẫn ngầm"]
  }}
]
"""

    @staticmethod
    def build_rules_prompt(idea: StoryIdea, world_info: Dict[str, Any]) -> str:
        """Step 1D: Sáng tạo Quy tắc thế giới quan (Rules & Memory) độc lập."""
        premise = world_info.get("premise", "Cốt truyện chính")
        return f"""=== STEP 1D: SÁNG TẠO QUY TẮC THẾ GIỚI QUAN ===
Nhiệm vụ: Sáng tạo 4 - 6 Quy tắc sắt bất biến kiểm soát thế giới quan dựa trên Tiền đề '{premise}'.

ĐẦU RA PHẢI LÀ MẢNG JSON CÁC QUY TẮC (TIẾNG VIỆT 100%):
[
  "Cấp độ sức mạnh tuân thủ nghiêm ngặt quy tắc đại lục",
  "Nhân vật không thể biết thông tin mà mình chưa từng tiếp xúc",
  "Tài nguyên quý hiếm đều bị các thế lực lớn kiểm soát",
  "Quy tắc sinh tồn và giao dịch trong thế giới"
]
"""

    @staticmethod
    def build_terminology_prompt(idea: StoryIdea, world_info: Dict[str, Any]) -> str:
        """Step 1E: Sáng tạo Từ điển Thuật ngữ đặc trưng thể loại độc lập."""
        return f"""=== STEP 1E: SÁNG TẠO TỪ ĐIỂN THUẬT NGỮ ===
Nhiệm vụ: Sáng tạo 5 - 8 Thuật ngữ đặc trưng riêng biệt của thể loại '{idea.genre}'.

ĐẦU RA PHẢI LÀ JSON OBJECT CÁC THUẬT NGỮ (TIẾNG VIỆT 100%):
{{
  "Thuật ngữ 1": "Mô tả ý nghĩa thuật ngữ 1",
  "Thuật ngữ 2": "Mô tả ý nghĩa thuật ngữ 2",
  "Thuật ngữ 3": "Mô tả ý nghĩa thuật ngữ 3",
  "Thuật ngữ 4": "Mô tả ý nghĩa thuật ngữ 4"
}}
"""
