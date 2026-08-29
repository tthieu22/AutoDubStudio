from typing import Dict, Any, List, Optional


class NovelRewriterPrompt:
    @staticmethod
    def build_prompt(
        chapter_num: int,
        scene_index: int,
        scene_plan: Dict[str, Any],
        draft_scene_text: str,
        issues: List[str],
        full_context: str,
        narrative_contract: Optional[Any] = None,
        progress_ledger: Optional[Any] = None,
        global_ledger: Optional[Any] = None
    ) -> str:
        issue_str = "\n".join([f"- {iss}" for iss in issues]) or "- Bản thảo bị lặp ý hoặc chưa đạt tiêu chuẩn Audio-First V2.3"
        scene_goal = scene_plan.get("goal", f"Phân cảnh {scene_index}")

        contract_str = ""
        if narrative_contract:
            forbidden = getattr(narrative_contract, "forbidden_topic_drift", []) if hasattr(narrative_contract, "forbidden_topic_drift") else narrative_contract.get("forbidden_topic_drift", [])
            contract_str = f"NARRATIVE CONTRACT (RÀNG BUỘC CẤM DRIFT): {forbidden}\n"

        return f"""# QWEN2.5 — SCENE REWRITER (SỬA LỖI PHÂN CẢNH V2.3)

Nhiệm vụ: Phân cảnh {scene_index} (Chương {chapter_num}) bị phát hiện LỖI NARRATIVE / REPETITION / NPC_CLAIM_LEAK.
Hãy SỬA LẠI bản thảo này sao cho giải quyết dứt điểm các lỗi được chỉ ra.

---

## 🛑 CÁC LỖI BẮT BUỘC PHẢI SỬA:
{issue_str}
{contract_str}

---

## QUY TẮC SỬA V2.3:
1. FIX ONLY THE IDENTIFIED PROBLEMS WITHOUT BREAKING CANON.
2. CẤM biến NPC Claims thành Confirmed Facts. NPC phỏng đoán thì nhân vật chỉ coi là phỏng đoán.
3. CẤM diễn đạt lại cùng một ý hay lặp lại sự kiện chương trước. Phải tạo tiến triển thực sự.
4. Đảm bảo câu ngắn vừa, nhịp điệu Audio-First sắc nét.

---

## MỤC TIÊU PHÂN CẢNH (SCENE GOAL):
- Phân cảnh: {scene_index} / Chương {chapter_num}
- Mục tiêu duy nhất: {scene_goal}

---

## BẢN THẢO BỊ LỖI CẦN SỬA:
{draft_scene_text}

---

# ĐẦU RA BẮT BUỘC
Chỉ output duy nhất nội dung phân cảnh đã sửa hoàn chỉnh.
Không output JSON, phân tích hay metadata.

Bắt đầu viết SCENE {scene_index} ĐÃ SỬA:"""


