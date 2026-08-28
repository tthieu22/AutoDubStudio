from typing import Dict, Any


class NovelWriterPrompt:
    @staticmethod
    def build_prompt(
        chapter_num: int,
        scene_index: int,
        scene_plan: Dict[str, Any],
        full_context: str
    ) -> str:
        return f"""
=== VAI TRÒ: NOVEL WRITER (NHÀ VĂN TIÊN HIỆP SÁNG TẠO) ===
Nhiệm vụ: Viết phân cảnh Scene {scene_index} cho Chương {chapter_num}.

BỐI CẢNH & THÔNG TIN BẮT BUỘC TUÂN THỦ (STORY MEMORY & CANON):
{full_context}

KẾ HOẠCH PHÂN CẢNH SCENE {scene_index}:
- Mục tiêu phân cảnh: {scene_plan.get('goal')}
- Cảm xúc chủ đạo: {scene_plan.get('emotion')}
- Xung đột/Trở ngại: {scene_plan.get('conflict')}
- Kết thúc Scene: {scene_plan.get('ending')}
- Dung lượng mục tiêu: ~{scene_plan.get('estimated_words', 600)} chữ

QUY TẮC VIẾT:
1. Áp dụng công thức: HOOK → PROBLEM → TENSION → REVEAL/PAYOFF → CLIFFHANGER.
2. Văn phong tự nhiên, hoa mỹ nhưng tiết tấu nhanh, nhiều đối thoại sắc bén.
3. Không phá vỡ Cảnh Giới hay Quy Tắc Thế Giới đã được thiết lập ở Canon.
4. Nhân vật CHỈ ĐƯỢC PHÁT NGÔN/HÀNH ĐỘNG dựa trên kiến thức họ ĐÃ BIẾT (xem Knowledge Boundary).

HÃY VIẾT NỘI DUNG VĂN HỌC CHI TIẾT CỦA SCENE {scene_index}:
"""
