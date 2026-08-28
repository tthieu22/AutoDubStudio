from typing import Dict, Any


class MemoryExtractorPrompt:
    @staticmethod
    def build_prompt(chapter_num: int, final_chapter_text: str) -> str:
        return f"""
=== VAI TRÒ: MEMORY EXTRACTOR (TRÍ TRÍ NHỚ & TRÍCH XUẤT CANON) ===
Nhiệm vụ: Phân tích Chương {chapter_num} và trích xuất dữ liệu cấu trúc để lưu vào Canon Database.

NỘI DUNG CHƯƠNG {chapter_num}:
{final_chapter_text}

YÊU CẦU ĐẦU RA (Trả về duy nhất 1 JSON Object):
{{
  "summary": "Tóm tắt 2-3 câu diễn biến chính của chương",
  "canon_facts": [
    {{
      "category": "realm_change",
      "fact_text": "Lâm Phàm đạt Trúc Cơ Tầng 2",
      "confidence": 1.0
    }},
    {{
      "category": "reveal",
      "fact_text": "Thanh Vân Quả có nguồn gốc từ Tiên Giới",
      "confidence": 0.95
    }}
  ],
  "character_changes": [
    {{
      "character_id": "char_001",
      "realm": "Trúc Cơ Tầng 2",
      "location": "Thanh Vân Tông",
      "new_known_info": ["Thanh Vân Quả là tiên vật"]
    }}
  ],
  "new_plot_threads": [
    {{
      "title": "Nguồn gốc thật của Thanh Vân Quả",
      "description": "Cần điều tra ai đã mang quả từ Tiên Giới xuống",
      "since_chapter": {chapter_num}
    }}
  ],
  "resolved_plot_threads": []
}}
"""
