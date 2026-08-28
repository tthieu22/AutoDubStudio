from typing import Dict, Any


class NovelScenePlannerPrompt:
    @staticmethod
    def build_prompt(chapter_num: int, chapter_plan: Dict[str, Any], creative_choice: Dict[str, Any]) -> str:
        return f"""
=== VAI TRÒ: SCENE PLANNER (PHÂN CHIA PHÂN CẢNH CHƯƠNG) ===
Nhiệm vụ: Chia Chương {chapter_num} thành 3-5 Phân Cảnh (Scenes) nhỏ (500-800 chữ/scene).

KẾ HOẠCH CHƯƠNG:
- Goal: {chapter_plan.get('goal')}
- Conflict: {chapter_plan.get('conflict')}
- Plot Twist đã chọn: {creative_choice.get('title')} - {creative_choice.get('description')}

YÊU CẦU ĐẦU RA (Trả về JSON Array các Scene):
[
  {{
    "scene_index": 1,
    "goal": "Phát hiện sự bất thường tại hiện trường",
    "emotion": "Nghi ngờ, đề phòng",
    "conflict": "Phát hiện có dấu vết kẻ lạ đột nhập",
    "reveal": null,
    "ending": "Nhận ra bản thân đã lọt vào trận pháp",
    "estimated_words": 600
  }},
  {{
    "scene_index": 2,
    "goal": "Giao phong và tìm đường thoát",
    "emotion": "Căng thẳng, kịch tính",
    "conflict": "Đối đầu với 2 đệ tử Ma Tông",
    "reveal": "Đối phương sở hữu pháp bảo chặn linh khí",
    "ending": "Lâm Phàm tung ra át chủ bài hệ thống",
    "estimated_words": 700
  }}
]
"""
