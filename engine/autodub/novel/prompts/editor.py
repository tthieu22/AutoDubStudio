from typing import Dict, Any


class NovelEditorPrompt:
    @staticmethod
    def build_prompt(chapter_num: int, draft_text: str) -> str:
        return f"""
=== VAI TRÒ: NOVEL EDITOR (BIÊN TẬP VIÊN VĂN HỌC) ===
Nhiệm vụ: Chỉnh sửa, gọt dũa và tối ưu bản thảo Chương {chapter_num}.

BẢN THẢO THÔ (DRAFT):
{draft_text}

TAY NGHỀ BIÊN TẬP KIỂM TRA:
□ Văn phong mượt mà, đậm chất tiên hiệp
□ Loại bỏ lặp từ, lặp ý
□ Tăng cường tự nhiên trong lời thoại nhân vật
□ Đảm bảo nhịp truyện căng thẳng, hấp dẫn
□ Giữ nguyên logic tình tiết và Cliffhanger ở cuối chương

YÊU CẦU ĐẦU RA (Trả về JSON Object):
{{
  "edited_text": "Nội dung chương sau khi đã biên tập hoàn chỉnh...",
  "changes_made": [
    "Sửa lặp từ ở đoạn 2",
    "Tối ưu lời thoại của Lâm Phàm sắc bén hơn"
  ],
  "quality_score": 9.2
}}
"""
