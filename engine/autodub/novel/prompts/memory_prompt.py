from typing import Dict, Any, List


class MemoryPrompt:
    @staticmethod
    def build_prompt(
        chapter_num: int,
        chapter_text: str,
        relevant_characters: List[Dict[str, Any]],
        known_memory: List[Dict[str, Any]],
        genre: str = "Tự do"
    ) -> str:
        chars_str = ", ".join([f"{c.get('id')}:{c.get('name')}" for c in relevant_characters]) or "Chưa có nhân vật"
        mem_str = "\n".join([f"- [{m.get('character_id')}] {m.get('fact_text')} ({m.get('information_state', 'CONFIRMED')})" for m in known_memory]) or "Chưa có ký ức cũ"

        return f"""=== DOMAIN ENGINE 03: MEMORY ENGINE (CHUYÊN GIA KIẾN THỨC & KÝ ỨC NHÂN VẬT) ===

[ROLE & MISSION]
- Vai trò: Chuyên gia Theo Dõi Ranh Giới Kiến Thức & Trạng Thái Thông Tin Nhân Vật (Memory & Knowledge Boundary Analyzer).
- Nhiệm vụ: Phân tích Chương {chapter_num} thuộc thể loại '{genre}' để xác định chính xác những tri thức/thông tin MỚI mà nhân vật tiếp nhận, đồng thời quản lý nghiêm ngặt Trạng Thái Thông Tin (Information State).

[STRICT INFORMATION STATES]
Mỗi tri thức trích xuất BẮT BUỘC phải gán đúng một trong các trạng thái sau:
1. UNKNOWN: Nhân vật chưa biết hoặc thông tin bị che giấu hoàn toàn.
2. RUMOR: Tin đồn lan truyền từ bên ngoài, chưa có căn cứ chứng minh.
3. CLAIM: Lời tuyên bố hoặc khẳng định từ một phía của ai đó (có thể nói dối hoặc lừa gạt).
4. CONFIRMED: Đã được xác thực chắc chắn (tận mắt thấy, tận tay sờ, bằng chứng không thể chối cãi).

[INPUT CONTRACT]
- Thể loại truyện: {genre}
- Chương hiện tại: {chapter_num}
- Nhân vật tham gia: {chars_str}
- Ký ức & Tri thức đã có trong Canon:
{mem_str}
- Bản thảo Chương {chapter_num}:
{chapter_text}

[ANTI-KNOWLEDGE LEAK & STATE TRANSITION RULES]
1. KHÔNG LEAK KÝ ỨC: Nhân vật A tiếp nhận thông tin KHÔNG CÓ NGHĨA Nhân vật B cũng biết. Ký ức phải gắn chặt với từng `character_id`.
2. CHUYỂN TRẠNG THÁI HỢP LỆ: Tuyệt đối CẤM tự ý chuyển `UNKNOWN -> CONFIRMED` nếu chương chỉ cung cấp tin đồn (`RUMOR`) hoặc lời nói từ một phía (`CLAIM`).
3. MỌI TRI THỨC PHẢI CÓ EVIDENCE: Phải trích dẫn đoạn văn chứng minh nhân vật đã nghe/thấy/học được tri thức đó.

[NEGATIVE RULES]
- KHÔNG biến lời nói dối của kẻ thù/NPC thành tri thức CONFIRMED của nhân vật chính.
- KHÔNG bịa ra tri thức nhân vật chưa tiếp xúc.

[OUTPUT CONTRACT (JSON SCHEMA)]
Trả về DUY NHẤT một JSON Object hợp lệ:
{{
  "memory_updates": [
    {{
      "character_id": "Mã ID nhân vật tiếp nhận tri thức (VD: char_001)",
      "fact_text": "Nội dung tri thức cụ thể nhân vật mới học được",
      "information_state": "RUMOR / CLAIM / CONFIRMED",
      "previous_state": "UNKNOWN / RUMOR / CLAIM",
      "evidence": {{
        "chapter": {chapter_num},
        "source": "dialogue / narration / secret_letter",
        "text_reference": "Câu trích dẫn chính xác trong bản thảo chương chứng minh nhân vật tiếp nhận thông tin"
      }}
    }}
  ]
}}
"""
