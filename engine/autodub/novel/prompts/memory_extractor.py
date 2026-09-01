from typing import Dict, Any


class MemoryExtractorPrompt:
    @staticmethod
    def build_prompt(chapter_num: int, final_chapter_text: str) -> str:
        return f"""
=== VAI TRÒ: MEMORY EXTRACTOR (TRÍCH XUẤT CANON & METADATA V2.3) ===
Nhiệm vụ: Phân tích Chương {chapter_num} (CHỈ ĐƯỢC TRÍCH XUẤT TỪ VĂN BẢN NÀY) và xuất dữ liệu cấu trúc.

CRITICAL RULES:
1. KHÔNG tự bịa facts hay suy đoán từ hidden reasoning.
2. Nếu một thông tin do NPC phát biểu/tuyên bố → `information_state`: "CLAIM", `source_speaker`: "Tên NPC".
3. Nếu là tin đồn chưa rõ nguồn → `information_state`: "RUMOR".
4. Nếu có cổ thư/bằng chứng trực tiếp → `information_state`: "EVIDENCE".
5. TUYỆT ĐỐI KHÔNG SET `information_state`: "CONFIRMED" (Chỉ Engine mới có quyền confirm).

NỘI DUNG CHƯƠNG {chapter_num}:
{final_chapter_text}

[OUTPUT CONTRACT - STRICT RAW JSON ONLY]
- Trả về DUY NHẤT 1 JSON Object hợp lệ theo cấu trúc mẫu sau.
- CẤM kèm bất kỳ lời dẫn, giải thích hay khối markdown codeblock (```json ... ```).
- ĐẦU RA BẮT ĐẦU BẰNG KÝ TỰ '{' VÀ KẾT THÚC BẰNG '}'.

CẤU TRÚC JSON MẪU:
{{
  "summary": "Tóm tắt 2-3 câu diễn biến chính của chương",
  "new_characters": [
    {{
      "name": "Tên NPC (Ví dụ: Thanh Viên, Đệ tử Chấp Pháp Đường)",
      "role_description": "Vai trò hoặc mô tả ngắn về NPC này"
    }}
  ],
  "new_discoveries": [
    {{
      "id": "mysterious_book",
      "name": "Tên vật phẩm/tài liệu/manh mối mới tìm thấy",
      "status": "UNTOUCHED"
    }}
  ],
  "canon_facts": [
    {{
      "category": "lore",
      "fact_text": "Mô tả sự thật / tuyên bố / bằng chứng",
      "information_state": "CLAIM",
      "source_speaker": "Tên NPC hoặc Narrator",
      "source_excerpt": "Trích đoạn ngắn từ chương chứa thông tin này",
      "confidence": 0.95
    }}
  ],
  "character_changes": [
    {{
      "character_id": "char_001",
      "realm": "Trúc Cơ Tầng 2",
      "location": "Thanh Vân Tông",
      "new_known_info": ["Thông tin nhân vật đã học"]
    }}
  ],
  "new_plot_threads": [
    {{
      "title": "Tên tuyến truyện mới mở",
      "description": "Mô tả tuyến truyện",
      "since_chapter": {chapter_num}
    }}
  ],
  "resolved_plot_threads": []
}}
"""

