from typing import Dict, Any
from autodub.novel.novel_models import StoryIdea


class StoryDirectorPrompt:
    @staticmethod
    def _get_target_counts(total_chapters: int) -> Dict[str, Any]:
        """Tính toán quy mô dữ liệu tối ưu dựa trên tổng số chương dự kiến."""
        chaps = max(10, total_chapters)
        if chaps <= 100:
            return {
                "factions_count": "2 - 4 thế lực chính",
                "locations_count": "2 - 4 địa danh trọng yếu",
                "ranks_count": 5,
                "ranks_desc": "5 - 7 cấp độ/cảnh giới chính",
                "chars_count": 4,
                "chars_desc": "4 - 5 nhân vật nòng cốt",
                "terms_count": 5
            }
        elif chaps <= 500:
            return {
                "factions_count": "4 - 6 thế lực chính (phù hợp với quy mô 500 chương)",
                "locations_count": "4 - 6 địa danh trọng yếu",
                "ranks_count": 8,
                "ranks_desc": "7 - 10 cấp độ/cảnh giới chính",
                "chars_count": 6,
                "chars_desc": "6 - 8 nhân vật nòng cốt (Đồng đội, Nữ chính, Sư phụ, Phản diện, Đối thủ)",
                "terms_count": 8
            }
        else:
            return {
                "factions_count": "6 - 10 thế lực chính (Thương hội, Cổ tộc, Chư thiên thế lực)",
                "locations_count": "6 - 10 địa danh từ Hạ giới đến Thượng giới",
                "ranks_count": 12,
                "ranks_desc": "10 - 15 cấp độ/cảnh giới tiến hóa dài hạn",
                "chars_count": 10,
                "chars_desc": "8 - 12 nhân vật nòng cốt (Đầy đủ Nam & Nữ, Phản diện qua từng thời kỳ)",
                "terms_count": 10
            }

    @staticmethod
    def build_prompt(idea: StoryIdea) -> str:
        """Tổng hợp prompt khởi tạo Bối cảnh thế giới & Hồ sơ truyện."""
        p_name = idea.protagonist.get("name", "Nhân vật chính") if isinstance(idea.protagonist, dict) else "Nhân vật chính"
        p_bg = idea.protagonist.get("background", "Bối cảnh ban đầu") if isinstance(idea.protagonist, dict) else "Bối cảnh ban đầu"
        total_chaps = getattr(idea, "total_chapters", 100)
        targets = StoryDirectorPrompt._get_target_counts(total_chaps)

        return f"""=== VAI TRÒ: STORY DIRECTOR (GIÁM ĐỐC SÁNG TẠO NỘI DUNG TRUYỆN MỚI) ===
Nhiệm vụ: Dựa trên Ý TƯỞNG CỦA NGHỆ SĨ và TỔNG SỐ CHƯƠNG DỰ KIẾN ({total_chaps} CHƯƠNG), hãy sáng tạo BỘ HỒ SƠ THẾ GIỚI & QUY TẮC TRUYỆN (STORY BIBLE) hoàn toàn mới, độc đáo, 100% phù hợp với thể loại và bối cảnh.

THÔNG TIN ĐẦU VÀO TỪ NGƯỜI DÙNG:
- Tên truyện: {idea.title}
- Thể loại: {idea.genre}
- Phong cách: {idea.style}
- Quy mô câu chuyện dự kiến: {total_chaps} chương
- Nhân vật chính: {p_name} ({p_bg})
- Yêu cầu đặc biệt: {", ".join(idea.requirements) if idea.requirements else "Sáng tạo độc đáo"}

QUY TẮC SÁNG TẠO BẮT BUỘC:
1. Tính toán quy mô dữ liệu phù hợp với bộ truyện {total_chaps} chương:
   - Hệ thống cảnh giới/cấp độ sức mạnh (`progression_system`): Sáng tạo {targets['ranks_desc']}.
   - Thế lực & Địa danh (`world`): Sáng tạo {targets['factions_count']}.
   - Dàn nhân vật (`characters`): Sáng tạo {targets['chars_desc']}.
2. NGUYÊN TẮC THIẾT KẾ MỞ (EXTENSIBLE): Thiết kế bối cảnh, cảnh giới và dàn nhân vật với cấu trúc mở, có thể tiếp tục mở rộng (đột phá Thượng giới / phát hiện địa danh mới) khi bộ truyện kéo dài thêm.
3. Nhân vật chính BẮT BUỘC là: '{p_name}'.
4. TOÀN BỘ NỘI DUNG VĂN BẢN TRONG ĐẦU RA JSON BẮT BUỘC PHẢI VIẾT 100% BẰNG TIẾNG VIỆT MƯỢT MÀ, TỰ NHIÊN. CẤM TRẢ VỀ TIẾNG ANH/TRUNG.

[OUTPUT CONTRACT - STRICT RAW JSON ONLY]
- Trả về DUY NHẤT 1 JSON Object hợp lệ ngắn gọn.
- CẤM kèm bất kỳ lời dẫn, giải thích hay khối markdown codeblock (```json ... ```).
- ĐẦU RA BẮT ĐẦU BẰNG KÝ TỰ '{' VÀ KẾT THÚC BẰNG '}'.

CẤU TRÚC JSON MẪU:
{{
  "premise": "Tóm tắt cốt truyện chủ đạo và bước ngoặt khởi đầu của {p_name}",
  "world": {{
    "continent_name": "Tên thế giới / đại lục / hành tinh chính",
    "factions": [
      "Thế lực khởi đầu / Tông môn chính",
      "Tổ chức phản diện / Ngầm"
    ],
    "locations": [
      "Vùng đất khởi đầu (Làng/Tân thủ/Trạm vũ trụ)",
      "Thành phố / Kinh thành trung tâm"
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
  "characters": [
    {{
      "id": "char_001",
      "name": "{p_name}",
      "gender": "Nam",
      "personality": ["Điềm tĩnh", "Quyết đoán"],
      "goal": "Mục tiêu lớn nhất của {p_name}",
      "realm": "Cấp độ khởi đầu",
      "location": "Vị trí khởi đầu",
      "known_information": ["{p_bg}"],
      "secrets": ["Bí mật lớn nhất / Kim thủ chỉ"]
    }},
    {{
      "id": "char_002",
      "name": "Nguyệt Nhi",
      "gender": "Nữ",
      "personality": ["Sắc sảo", "Trung thành"],
      "goal": "Sát cánh và hỗ trợ {p_name}",
      "realm": "Cấp độ khởi đầu",
      "location": "Vị trí khởi đầu",
      "known_information": ["Bối cảnh thân thế nữ đồng đội"],
      "secrets": ["Bí mật gia thế / Manh mối cổ xưa"]
    }}
  ],
  "rules": [
    "Cấp độ tuân thủ nghiêm ngặt theo quy tắc thế giới",
    "Nhân vật không thể biết thông tin mà mình chưa từng tiếp xúc"
  ]
}}
"""

    @staticmethod
    def build_world_prompt(idea: StoryIdea) -> str:
        """Step 1A: Prompt dành riêng cho Bối cảnh thế giới & Tiền đề."""
        p_name = idea.protagonist.get("name", "Nhân vật chính") if isinstance(idea.protagonist, dict) else "Nhân vật chính"
        p_bg = idea.protagonist.get("background", "Bối cảnh ban đầu") if isinstance(idea.protagonist, dict) else "Bối cảnh ban đầu"
        total_chaps = getattr(idea, "total_chapters", 100)
        targets = StoryDirectorPrompt._get_target_counts(total_chaps)

        return f"""=== VAI TRÒ: STORY DIRECTOR (STEP 1A: BỐI CẢNH THẾ GIỚI & TIỀN ĐỀ - QUY MÔ {total_chaps} CHƯƠNG) ===
Nhiệm vụ: Sáng tạo BỐI CẢNH THẾ GIỚI & TIỀN ĐỀ CỐT TRUYỆN độc đáo cho tác phẩm '{idea.title}' (Thể loại: {idea.genre}, Phong cách: {idea.style}, Quy mô dự kiến: {total_chaps} chương).

THÔNG TIN NHÂN VẬT CHÍNH:
- Tên: {p_name}
- Thân thế khởi đầu: {p_bg}

QUY TẮC SÁNG TẠO HỆ THỐNG MỞ (EXTENSIBLE):
1. Sáng tạo tên đại lục / thế giới / hành tinh mới mẻ, hấp dẫn.
2. Sáng tạo {targets['factions_count']}.
3. Sáng tạo {targets['locations_count']}.
4. ĐẢM BẢO CẤU TRÚC MỞ: Bối cảnh thế giới quan được thiết kế có thể dễ dàng mở rộng sang các đại lục/thượng giới mới khi bộ truyện phát triển vượt mốc {total_chaps} chương.
5. TOÀN BỘ NỘI DUNG VIẾT BẰNG TIẾNG VIỆT 100%.

[OUTPUT CONTRACT - STRICT RAW JSON ONLY]
- Trả về DUY NHẤT 1 JSON Object hợp lệ.
- CẤM kèm bất kỳ lời dẫn, giải thích hay khối markdown codeblock (```json ... ```).
- ĐẦU RA BẮT ĐẦU BẰNG KÝ TỰ '{' VÀ KẾT THÚC BẰNG '}'.

CẤU TRÚC JSON MẪU:
{{
  "premise": "Tóm tắt ngắn gọn 2-3 câu về cốt truyện chủ đạo và bước ngoặt khởi đầu của {p_name}",
  "world": {{
    "continent_name": "Tên thế giới / đại lục chính",
    "factions": [
      "Thế lực khởi đầu / Tông môn chính",
      "Tổ chức phản diện / Ngầm"
    ],
    "locations": [
      "Vùng đất khởi đầu (Làng/Tân thủ/Trạm vũ trụ)",
      "Thành phố / Kinh thành trung tâm"
    ]
  }}
}}
"""

    @staticmethod
    def build_progression_prompt(idea: StoryIdea, world_info: Dict[str, Any] | str) -> str:
        """Step 1B: Sáng tạo Hệ thống Cấp độ / Cảnh giới dựa trên bối cảnh đã có ở Step 1A và quy mô chương."""
        total_chaps = getattr(idea, "total_chapters", 100)
        targets = StoryDirectorPrompt._get_target_counts(total_chaps)

        if isinstance(world_info, str):
            premise = world_info
            continent = "Thế giới chính"
            factions = "Các thế lực lớn"
        else:
            premise = world_info.get("premise", "Cốt truyện chính")
            world_obj = world_info.get("world", {}) if isinstance(world_info.get("world"), dict) else {}
            continent = world_obj.get("continent_name", "Thế giới chính")
            factions = ", ".join(world_obj.get("factions", [])) if world_obj.get("factions") else "Các thế lực lớn"

        return f"""=== VAI TRÒ: STORY DIRECTOR (STEP 1B: HỆ THỐNG CẤP ĐỘ SỨC MẠNH - QUY MÔ {total_chaps} CHƯƠNG) ===
Nhiệm vụ: Sáng tạo hệ thống tiến trình sức mạnh ({targets['ranks_desc']}) CHUẨN XÁC THEO THỂ LOẠI '{idea.genre}' CHO BỘ TRUYỆN DỰ KIẾN {total_chaps} CHƯƠNG.

THÔNG TIN BỐI CẢNH ĐÃ TẠO TỪ STEP 1A:
- Tiền đề cốt truyện: {premise}
- Thế giới / Đại lục: {continent}
- Các thế lực chính: {factions}

QUY TẮC BẮT BUỘC & TÍNH TOÁN DỮ LIỆU:
1. Sáng tạo chính xác {targets['ranks_desc']} tương ứng với lộ trình phát triển trong {total_chaps} chương.
2. NGUYÊN TẮC HỆ THỐNG MỞ (EXTENSIBLE): Thiết kế các cấp độ có tính kế thừa và có tầng giới hạn mở (Thượng giới / Thần giới / Cảnh giới ẩn) để sẵn sàng mở rộng thêm khi tác giả muốn viết tiếp.
3. Thể loại Tiên Hiệp/Huyền Huyễn: type='cultivation', ranks chuẩn cổ trang.
4. Thể loại Sci-Fi/Vũ Trụ: type='technology', ranks chuẩn khoa học kỹ thuật.
5. Thể loại Game/Dị Năng: type='level', ranks chuẩn F-Rank đến SSS-Rank.
6. TOÀN BỘ NỘI DUNG VIẾT BẰNG TIẾNG VIỆT 100%.

[OUTPUT CONTRACT - STRICT RAW JSON ONLY]
- Trả về DUY NHẤT 1 JSON Object hợp lệ.
- CẤM kèm bất kỳ lời dẫn, giải thích hay khối markdown codeblock (```json ... ```).
- ĐẦU RA BẮT ĐẦU BẰNG KÝ TỰ '{' VÀ KẾT THÚC BẰNG '}'.

CẤU TRÚC JSON MẪU:
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
        """Step 1C: Sáng tạo Dàn nhân vật nòng cốt dựa trên Bối cảnh (1A), Cảnh giới (1B) & Quy mô chương."""
        total_chaps = getattr(idea, "total_chapters", 100)
        targets = StoryDirectorPrompt._get_target_counts(total_chaps)

        p_name = idea.protagonist.get("name", "Nhân vật chính") if isinstance(idea.protagonist, dict) else "Nhân vật chính"
        p_bg = idea.protagonist.get("background", "Bối cảnh ban đầu") if isinstance(idea.protagonist, dict) else "Bối cảnh ban đầu"
        premise = world_info.get("premise", "Cốt truyện chính")
        world_obj = world_info.get("world", {}) if isinstance(world_info.get("world"), dict) else {}
        continent = world_obj.get("continent_name", "Thế giới")
        factions = ", ".join(world_obj.get("factions", [])) if world_obj.get("factions") else "Các thế lực chính"

        prog_ranks = []
        prog_sys = world_info.get("progression_system", {})
        if isinstance(prog_sys, dict) and "ranks" in prog_sys and isinstance(prog_sys["ranks"], list):
            prog_ranks = [r.get("name") for r in prog_sys["ranks"] if isinstance(r, dict) and r.get("name")]
        if not prog_ranks:
            prog_ranks = [c.get("name") for c in world_info.get("cultivation_system", []) if isinstance(c, dict) and c.get("name")]
        rank_str = ", ".join(prog_ranks[:4]) if prog_ranks else "Cấp 1 Khởi Đầu, Cấp 2 Tiến Bổn"

        return f"""=== VAI TRÒ: STORY DIRECTOR (STEP 1C: DÀN NHÂN VẬT THẾ GIỚI QUAN - QUY MÔ {total_chaps} CHƯƠNG) ===
Nhiệm vụ: Hãy sáng tạo DÀN NHÂN VẬT NÒNG CỐT ({targets['chars_desc']}) bám sát bối cảnh, hệ thống cảnh giới và quy mô dự kiến {total_chaps} chương.

THÔNG TIN ĐÃ TẠO TỪ STEP 1A & 1B:
- Cốt truyện & Tiền đề: {premise}
- Đại lục / Thế giới: {continent} | Thế lực chính: {factions}
- Hệ thống cảnh giới / cấp độ sức mạnh: {rank_str}

QUY TẮC BẮT BUỘC & TÍNH TOÁN DỮ LIỆU:
1. Sáng tạo {targets['chars_desc']} (Bao gồm Cả Nam & Nữ: Đồng đội, Nữ chính, Phản diện, Sư phụ/Tiền bối, Đối thủ cạnh tranh).
2. CẤM TRÙNG TÊN: MỖI NHÂN VẬT BẮT BUỘC PHẢI CÓ TÊN RIÊNG ĐỘC NHẤT (UNIQUE NAME). Tuyệt đối CẤM tạo 2 nhân vật cùng tên hoặc lặp lại họ tên (Ví dụ: CẤM tạo 2 nhân vật cùng tên 'Thiên Phong').
3. ĐA DẠNG HÓA VAI TRÒ & ĐỘ TUỔI: Độ tuổi (18, 25, 45, 60,...), vai trò (Nữ chính, Phản diện, Sư phụ, Bằng hữu, Trưởng lão...), tính cách và bối cảnh của mỗi nhân vật phải hoàn toàn khác biệt. CẤM để tất cả nhân vật có cùng 1 tuổi hay mô tả giống hệt nhau.
4. NGUYÊN TẮC HỆ THỐNG MỞ (EXTENSIBLE): Tạo các tuyến nhân vật có tiềm năng phát triển lâu dài, mở đường cho việc bổ sung thêm các nhân vật phụ ở từng Arc trong tương lai.
5. Cảnh giới (`realm`) của mỗi nhân vật PHẢI sử dụng đúng tên các cấp độ sức mạnh vừa tạo ({rank_str}).
6. Nhân vật chính BẮT BUỘC là: '{p_name}' ({p_bg}).
7. Tên nhân vật phải tự nhiên, hợp thể loại '{idea.genre}'. CẤM dùng các từ giữ chỗ 'Tính cách 1', 'Địa danh 1'.
8. TOÀN BỘ VIẾT BẰNG TIẾNG VIỆT 100%.

[OUTPUT CONTRACT - STRICT RAW JSON ONLY]
- Trả về DUY NHẤT 1 Mảng JSON (JSON Array) hợp lệ.
- CẤM kèm bất kỳ lời dẫn, giải thích hay khối markdown codeblock (```json ... ```).
- ĐẦU RA BẮT ĐẦU BẰNG KÝ TỰ '[' VÀ KẾT THÚC BẰNG ']'.

CẤU TRÚC JSON MẪU:
[
  {{
    "id": "char_001",
    "name": "{p_name}",
    "gender": "Nam",
    "age": "21",
    "role": "Nhân vật chính",
    "personality": ["Điềm tĩnh", "Thông minh", "Quyết đoán"],
    "appearance": "Thân hình thon gọn, ánh mắt sắc bén, thần thái kiên định",
    "clothing": "Y phục thanh nhã phong trần",
    "goal": "Mục tiêu lớn nhất của {p_name}",
    "realm": "Cấp độ 1 Khởi Đầu",
    "location": "Vị trí khởi đầu",
    "known_information": ["{p_bg}"],
    "secrets": ["Kim thủ chỉ / Bí mật lớn"]
  }},
  {{
    "id": "char_002",
    "name": "Nguyệt Nhi",
    "gender": "Nữ",
    "age": "19",
    "role": "Nữ chính / Đồng đội",
    "personality": ["Sắc sảo", "Thông minh", "Trung thành"],
    "appearance": "Dáng người thanh tú, ánh mắt rạng rỡ",
    "clothing": "Váy lụa xanh biếc nhã nhặn",
    "goal": "Sát cánh hỗ trợ {p_name}",
    "realm": "Cấp độ 1 Khởi Đầu",
    "location": "Vị trí khởi đầu",
    "known_information": ["Gia thế đồng đội"],
    "secrets": ["Bí mật gia thế / Manh mối cổ"]
  }}
]
"""

    @staticmethod
    def build_rules_prompt(idea: StoryIdea, world_info: Dict[str, Any]) -> str:
        """Step 1D: Sáng tạo Quy tắc thế giới quan dựa trên Bối cảnh (1A), Cảnh giới (1B) & Nhân vật (1C)."""
        total_chaps = getattr(idea, "total_chapters", 100)
        premise = world_info.get("premise", "Cốt truyện chính")
        world_obj = world_info.get("world", {}) if isinstance(world_info.get("world"), dict) else {}
        continent = world_obj.get("continent_name", "Thế giới")

        chars = world_info.get("characters", [])
        char_names = ", ".join([c.get("name") for c in chars if isinstance(c, dict) and c.get("name")]) if chars else "Các nhân vật nòng cốt"

        return f"""=== VAI TRÒ: STORY DIRECTOR (STEP 1D: QUY TẮC THẾ GIỚI QUAN - QUY MÔ {total_chaps} CHƯƠNG) ===
Nhiệm vụ: Sáng tạo 4 - 8 Quy tắc sắt bất biến kiểm soát thế giới quan dựa trên bối cảnh, quy mô {total_chaps} chương và dàn nhân vật vừa tạo.

THÔNG TIN ĐÃ TẠO TỪ STEP 1A, 1B, 1C:
- Tiền đề cốt truyện: {premise}
- Đại lục: {continent}
- Dàn nhân vật nòng cốt: {char_names}

QUY TẮC SÁNG TẠO:
1. Quy tắc phải ăn khớp với mâu thuẫn chính và thế giới quan '{continent}'.
2. CẤM LẶP LẠI CÁC CÂU MẪU: Mỗi quy tắc trong mảng BẮT BUỘC phải có nội dung ĐỘC NHẤT (Unique), cấm lặp đi lặp lại cùng một câu hay cùng một ý.
3. ĐẢM BẢO QUY TẮC CÓ TÍNH MỞ (Extensible): Bao gồm quy tắc về thăng cấp, ranh giới sinh tử, và quy luật phát triển dài hạn.
4. TOÀN BỘ NỘI DUNG VIẾT BẰNG TIẾNG VIỆT 100%.

[OUTPUT CONTRACT - STRICT RAW JSON ONLY]
- Trả về DUY NHẤT 1 Mảng JSON (JSON Array) hợp lệ.
- CẤM kèm bất kỳ lời dẫn, giải thích hay khối markdown codeblock (```json ... ```).
- ĐẦU RA BẮT ĐẦU BẰNG KÝ TỰ '[' VÀ KẾT THÚC BẰNG ']'.

CẤU TRÚC JSON MẪU:
[
  "Cấp độ sức mạnh tuân thủ nghiêm ngặt quy tắc đại lục {continent}",
  "Nhân vật không thể biết thông tin mà mình chưa từng tiếp xúc trực tiếp",
  "Tài nguyên tu luyện quý hiếm đều bị các đại thế lực kiểm soát gắt gao",
  "Ranh giới sinh tử giữa các cảnh giới không thể dễ dàng vượt qua bằng ngoại lực"
]
"""

    @staticmethod
    def build_terminology_prompt(idea: StoryIdea, world_info: Dict[str, Any]) -> str:
        """Step 1E: Sáng tạo Từ điển Thuật ngữ dựa trên Thế giới quan toàn diện (1A - 1D)."""
        total_chaps = getattr(idea, "total_chapters", 100)
        targets = StoryDirectorPrompt._get_target_counts(total_chaps)

        premise = world_info.get("premise", "Cốt truyện chính")
        world_obj = world_info.get("world", {}) if isinstance(world_info.get("world"), dict) else {}
        continent = world_obj.get("continent_name", "Thế giới")
        factions = ", ".join(world_obj.get("factions", [])) if world_obj.get("factions") else "Các thế lực chính"

        prog_ranks = []
        prog_sys = world_info.get("progression_system", {})
        if isinstance(prog_sys, dict) and "ranks" in prog_sys and isinstance(prog_sys["ranks"], list):
            prog_ranks = [r.get("name") for r in prog_sys["ranks"] if isinstance(r, dict) and r.get("name")]
        rank_str = ", ".join(prog_ranks) if prog_ranks else "Các cảnh giới sức mạnh"

        return f"""=== VAI TRÒ: STORY DIRECTOR (STEP 1E: TỪ ĐIỂN THUẬT NGỮ) ===
Nhiệm vụ: Tạo {targets['terms_count']} thuật ngữ đặc trưng cho truyện '{idea.title}' (thể loại '{idea.genre}').

BỐI CẢNH:
- Đại lục: {continent}
- Cảnh giới: {rank_str}

QUY TẮC:
1. Mỗi thuật ngữ là 1 cặp "tên": "định nghĩa ngắn".
2. TOÀN BỘ TIẾNG VIỆT 100%.

[OUTPUT CONTRACT - STRICT RAW JSON ONLY]
- Trả về DUY NHẤT 1 JSON Object phẳng duy nhất (không có mục con).
- CẤM kèm bất kỳ lời dẫn, giải thích hay khối markdown codeblock (```json ... ```).
- ĐẦU RA BẮT ĐẦU BẰNG KÝ TỰ '{' VÀ KẾT THÚC BẰNG '}'.

CẤU TRÚC JSON MẪU:
{{
  "linh khí": "Năng lượng cơ bản của tu luyện",
  "đan dược": "Thuốc tăng lực từ thảo dược quý",
  "kiếm khí": "Năng lượng chiến đấu từ kiếm pháp"
"""

    @staticmethod
    def build_terminology_prompt(idea: StoryIdea, world_info: Dict[str, Any]) -> str:
        """Step 1E: Sáng tạo Từ điển Thuật ngữ dựa trên Thế giới quan toàn diện (1A - 1D)."""
        total_chaps = getattr(idea, "total_chapters", 100)
        targets = StoryDirectorPrompt._get_target_counts(total_chaps)

        premise = world_info.get("premise", "Cốt truyện chính")
        world_obj = world_info.get("world", {}) if isinstance(world_info.get("world"), dict) else {}
        continent = world_obj.get("continent_name", "Thế giới")
        factions = ", ".join(world_obj.get("factions", [])) if world_obj.get("factions") else "Các thế lực chính"

        prog_ranks = []
        prog_sys = world_info.get("progression_system", {})
        if isinstance(prog_sys, dict) and "ranks" in prog_sys and isinstance(prog_sys["ranks"], list):
            prog_ranks = [r.get("name") for r in prog_sys["ranks"] if isinstance(r, dict) and r.get("name")]
        rank_str = ", ".join(prog_ranks) if prog_ranks else "Các cảnh giới sức mạnh"

        return f"""=== VAI TRÒ: STORY DIRECTOR (STEP 1E: TỪ ĐIỂN THUẬT NGỮ) ===
Nhiệm vụ: Tạo {targets['terms_count']} thuật ngữ đặc trưng cho truyện '{idea.title}' (thể loại '{idea.genre}').

BỐI CẢNH:
- Đại lục: {continent}
- Cảnh giới: {rank_str}

QUY TẮC:
1. Mỗi thuật ngữ là 1 cặp "tên": "định nghĩa ngắn".
2. TOÀN BỘ TIẾNG VIỆT 100%.
3. ĐẦU RA LÀ 1 JSON OBJECT PHẲNG DUY NHẤT, KHÔNG CÓ MỤC CON.

MẪU ĐẦU RA:
{{
  "linh khí": "Năng lượng cơ bản của tu luyện",
  "đan dược": "Thuốc tăng lực từ thảo dược quý",
  "kiếm khí": "Năng lượng chiến đấu từ kiếm pháp"
}}
"""
