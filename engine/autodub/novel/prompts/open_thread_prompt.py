from typing import Dict, Any, List


class OpenThreadPrompt:
    @staticmethod
    def build_prompt(
        chapter_num: int,
        chapter_text: str,
        active_threads: List[Dict[str, Any]],
        genre: str = "Tự do"
    ) -> str:
        threads_str = "\n".join([f"- [{t.get('thread_id', 'thr')}] {t.get('title')}: {t.get('status')} ({t.get('description', '')})" for t in active_threads]) or "Chưa có tuyến kịch bản mở trong Canon"

        return f"""=== DOMAIN ENGINE 08: OPEN THREAD ENGINE (CHUYÊN GIA TUYẾN KỊCH BẢN & MỐ́I NGHI VẤN) ===

[ROLE & MISSION]
- Vai trò: Chuyên gia Theo Dõi & Quản Lý Mạch Kịch Bản Mở (Narrative Open Thread Analyzer).
- Nhiệm vụ: Phân tích Chương {chapter_num} thuộc thể loại '{genre}' để mở tuyến kịch bản MỚI, thúc đẩy các tuyến kịch bản ĐANG CHẠY, hoặc đóng/giải quyết các tuyến kịch bản ĐÃ HOÀN THÀNH.

[THREAD STATUS LIFECYCLE]
1. NEW: Manh mối / Bí ẩn / Nhiệm vụ / Nguy cơ mới xuất hiện trong chương.
2. ACTIVE: Tuyến kịch bản đang diễn ra.
3. PROGRESSING: Tuyến kịch bản cũ vừa có bước tiến đột phá quan trọng trong chương này.
4. RESOLVED: Bí ẩn đã được giải mã / Kẻ thù đã bị đánh bại / Nhiệm vụ đã hoàn thành triệt để.
5. CANCELLED: Tuyến kịch bản bị hủy bỏ hoặc không còn giá trị.

[INPUT CONTRACT]
- Thể loại truyện: {genre}
- Chương hiện tại: {chapter_num}
- Tuyến kịch bản mở hiện có trong Canon:
{threads_str}
- Bản thảo Chương {chapter_num}:
{chapter_text}

[DYNAMIC THREAD RULES]
1. KHÔNG MỞ TUYẾN KỊCH BẢN VỤN VẶN: Chỉ tạo tuyến kịch bản mở mới (`NEW`) cho các mối nghi vấn hoặc mục tiêu có sức ảnh hưởng đến các chương kế tiếp.
2. CẬP NHẬT TRẠNG THÁI CHÍNH XÁC: Nếu bí ẩn hay nhiệm vụ cũ được làm sáng tỏ trong chương này, BẮT BUỘC cập nhật `status: RESOLVED`.

[EVIDENCE MANDATE]
1. Mọi mở mới hay giải quyết tuyến kịch bản BẮT BUỘC phải kèm `evidence` trích dẫn chính xác trong chương.
2. Nếu không có biến động tuyến kịch bản nào, trả về mảng rỗng: "open_thread_updates": [].

[OUTPUT CONTRACT - STRICT RAW JSON ONLY]
- Trả về DUY NHẤT 1 JSON Object hợp lệ theo cấu trúc mẫu sau.
- CẤM kèm bất kỳ lời dẫn, giải thích hay khối markdown codeblock (```json ... ```).
- ĐẦU RA BẮT ĐẦU BẰNG KÝ TỰ '{' VÀ KẾT THÚC BẰNG '}'.

CẤU TRÚC JSON MẪU:
{{
  "open_thread_updates": [
    {{
      "thread_id": "Mã ID tuyến kịch bản (VD: thr_ch{chapter_num}_01 hoặc thr_001)",
      "title": "Tên tuyến kịch bản / Mối nghi vấn ngắn gọn",
      "status": "NEW / ACTIVE / PROGRESSING / RESOLVED / CANCELLED",
      "description": "Mô tả ngắn về tình trạng kịch bản trong chương",
      "evidence": {{
        "chapter": {chapter_num},
        "source": "narration / dialogue",
        "text_reference": "Câu trích dẫn chứng minh sự mở mới hoặc giải quyết tuyến kịch bản"
      }}
    }}
  ]
}}
"""
