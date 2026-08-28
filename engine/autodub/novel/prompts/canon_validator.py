from typing import Dict, Any, List


class CanonValidatorPrompt:
    @staticmethod
    def build_prompt(
        chapter_num: int,
        draft_text: str,
        relevant_canon: List[Dict[str, Any]],
        knowledge_map: Dict[str, Any]
    ) -> str:
        canon_str = "\n".join([f"- [{c.get('category')}] {c.get('fact_text')}" for c in relevant_canon]) or "Chưa có canon cũ"
        knowledge_str = "\n".join([f"- {char}: Đã biết {info.get('known')}, Chưa biết {info.get('unknown')}" for char, info in knowledge_map.items()]) or "Chưa rõ"

        return f"""
=== VAI TRÒ: CANON VALIDATOR (KỂM SOÁT TÍNH NHẤT QUÁN & LỖI LOGIC) ===
Nhiệm vụ: Thẩm định bản thảo Chương {chapter_num} đối chiếu với Dữ Liệu Canon Database và Ranh Giới Kiến Thức (Knowledge Boundary).

DỮ LIỆU CANON ĐÃ THIẾT LẬP:
{canon_str}

RANH GIỚI KIẾN THỨC NHÂN VẬT:
{knowledge_str}

BẢN THẢO CHƯƠNG {chapter_num}:
{draft_text}

QUY TẮC THẨM ĐỊNH:
1. Nhân vật KHÔNG ĐƯỢC phát ngôn hay hành động sử dụng thông tin thuộc danh sách "Chưa biết".
2. Cảnh giới nhân vật KHÔNG ĐƯỢC tự ý tăng/giảm mâu thuẫn với Canon.
3. Sự kiện không được mâu thuẫn với các Canon Fact đã xảy ra ở các chương trước.

YÊU CẦU ĐẦU RA (Trả về JSON Object):
{{
  "passed": true,
  "violations": [
    {{
      "rule": "Knowledge Boundary Violation",
      "severity": "ERROR",
      "message": "Lâm Phàm biết Tần Dao là hậu nhân Tiên Đế ở chương 500 là mâu thuẫn vì đến chương này Lâm Phàm chưa biết bí mật này",
      "suggestion": "Sửa lời thoại của Lâm Phàm thành chỉ nghi ngờ về thân thế Tần Dao"
    }}
  ]
}}
"""
