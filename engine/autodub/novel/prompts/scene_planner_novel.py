from typing import Dict, Any, Optional


class NovelScenePlannerPrompt:
    @staticmethod
    def build_prompt(chapter_num: int, chapter_plan: Dict[str, Any], context_summary: str = "") -> str:
        goal_text = chapter_plan.get('goal') if isinstance(chapter_plan, dict) else str(chapter_plan)
        conflict_text = chapter_plan.get('conflict', 'Xung đột cốt truyện') if isinstance(chapter_plan, dict) else 'Xung đột cốt truyện'

        return f"""=== VAI TRÒ: SCENE PLANNER (PHÂN CHIA PHÂN CẢNH AUDIO-FIRST) ===
Nhiệm vụ: Phân chia Chương {chapter_num} thành các Phân Cảnh (Scenes) hợp lý dựa STRICTLY trên Chapter Goal.
Không ép cố định số scene. Hãy phân chia tự nhiên theo dung lượng nội dung (thường từ 3 đến 6 scenes).

BỐI CẢNH & CANON HIỆN TẠI:
{context_summary}

MỤC TIÊU CHƯƠNG (CHAPTER GOAL):
- Goal: {goal_text}
- Conflict: {conflict_text}

QUY TẮC PHÂN CẢNH:
1. Mỗi scene phải có một mục tiêu cụ thể (Scene Goal) đóng góp trực tiếp cho Chapter Goal.
2. Không tạo scene filler chỉ để tăng chữ.
3. Ưu tiên các tình huống có đối thoại, hành động và cảm xúc tự nhiên.

[OUTPUT CONTRACT - STRICT RAW JSON ONLY]
- Trả về DUY NHẤT 1 Mảng JSON (JSON Array) hợp lệ.
- CẤM kèm bất kỳ lời dẫn, giải thích hay khối markdown codeblock (```json ... ```).
- ĐẦU RA BẮT ĐẦU BẰNG KÝ TỰ '[' VÀ KẾT THÚC BẰNG ']'.

CẤU TRÚC JSON MẪU:
[
  {{
    "scene_index": 1,
    "goal": "Mục tiêu cụ thể phân cảnh 1",
    "emotion": "Cảm xúc chủ đạo",
    "conflict": "Xung đột trong cảnh",
    "ending": "Điểm kết thúc/chuyển tiếp phân cảnh 1",
    "estimated_words": 500
  }},
  {{
    "scene_index": 2,
    "goal": "Mục tiêu cụ thể phân cảnh 2",
    "emotion": "Cảm xúc chủ đạo",
    "conflict": "Xung đột trong cảnh",
    "ending": "Điểm kết thúc/chuyển tiếp phân cảnh 2",
    "estimated_words": 600
  }}
]
"""


