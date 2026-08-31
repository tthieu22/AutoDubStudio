from typing import Dict, Any, List


class EventPrompt:
    @staticmethod
    def build_prompt(
        chapter_num: int,
        chapter_text: str,
        recent_events: List[Dict[str, Any]],
        genre: str = "Tự do"
    ) -> str:
        events_str = "\n".join([f"- [{e.get('event_id', 'evt')}] {e.get('title', 'Sự kiện')}: Trạng thái {e.get('status', 'FACT')}" for e in recent_events]) or "Chưa có sự kiện trong Canon"

        return f"""=== DOMAIN ENGINE 06: EVENT ENGINE (CHUYÊN GIA DIỄN BIẾN & NIÊN ĐẠI SỰ KIỆN) ===

[ROLE & MISSION]
- Vai trò: Chuyên gia Phân Tích Niên Đại & Diễn Biến Sự Kiện Trọng Đại (Event Chronology Analyzer).
- Nhiệm vụ: Phân tích Chương {chapter_num} thuộc thể loại '{genre}' để ghi nhận các sự kiện quan trọng MỚI đã diễn ra hoặc chuyển đổi trạng thái của sự kiện (FACT / CLAIM / RUMOR / UNKNOWN).

[STRICT EVENT STATUS]
1. FACT: Sự kiện đã xảy ra trực tiếp trong chương, được người kể chuyện (narration) hoặc nhiều nhân vật trực tiếp chứng kiến.
2. CLAIM: Sự kiện do một nhân vật kể lại hoặc khẳng định (chưa chắc là sự thật).
3. RUMOR: Sự kiện dạng tin đồn thiên hạ đồn đại.
4. UNKNOWN: Sự kiện bí ẩn chưa thể xác minh.

[INPUT CONTRACT]
- Thể loại truyện: {genre}
- Chương hiện tại: {chapter_num}
- Sự kiện quan trọng gần đây trong Canon:
{events_str}
- Bản thảo Chương {chapter_num}:
{chapter_text}

[DYNAMIC EVENT EXTRACTION RULES]
1. CHỈ GHI NHẬN SỰ KIỆN TRỌNG ĐẠI: Không trích xuất các hành động vặt vãnh (VD: 'Diệp Phàm uống trà', 'Lâm Phàm bước ra cửa'). Chỉ ghi nhận các cột mốc xoay chuyển diễn biến câu chuyện (VD: 'Cuộc phục kích tại hẻm núi', 'Sự cố vỡ lò phản ứng', 'Trận chiến đại bão').
2. TÊN SỰ KIỆN SẮC SẢO: Đặt tên tiêu đề sự kiện cô đọng, sắc sảo, tôn trọng thể loại '{genre}'.

[EVIDENCE MANDATE]
1. Mỗi sự kiện BẮT BUỘC phải kèm `evidence` trích dẫn chính xác đoạn văn bản xảy ra sự kiện.
2. Nếu chương chỉ là hội thoại bình thường không có biến cố lớn, trả về mảng rỗng: "event_updates": [].

[OUTPUT CONTRACT (JSON SCHEMA)]
Trả về DUY NHẤT một JSON Object hợp lệ:
{{
  "event_updates": [
    {{
      "event_id": "Mã ID sự kiện (VD: evt_ch{chapter_num}_01)",
      "title": "Tiêu đề sự kiện ngắn gọn sắc sảo",
      "summary": "Tóm tắt ngắn gọn diễn biến cốt lõi của sự kiện",
      "status": "FACT / CLAIM / RUMOR",
      "participants": ["Danh sách nhân vật tham gia"],
      "evidence": {{
        "chapter": {chapter_num},
        "source": "narration / action",
        "text_reference": "Câu trích dẫn chính xác trong bản thảo chương"
      }}
    }}
  ]
}}
"""
