from typing import Dict, Any, Optional, List


class NovelWriterPrompt:
    @staticmethod
    def build_prompt(
        chapter_num: int,
        scene_index: int,
        scene_plan: Dict[str, Any],
        full_context: str,
        chapter_goal: str = "",
        previous_scene_summary: str = "",
        narrative_contract: Optional[Any] = None,
        progress_ledger: Optional[Any] = None,
        global_ledger: Optional[Any] = None
    ) -> str:
        scene_goal = scene_plan.get("goal", f"Thực hiện phân cảnh {scene_index}")
        scene_emotion = scene_plan.get("emotion", "Căng thẳng")
        scene_conflict = scene_plan.get("conflict", "Xung đột tự nhiên")
        scene_ending = scene_plan.get("ending", "Chuyển tiếp hồi hộp")
        estimated_words = scene_plan.get("estimated_words", 600)

        contract_str = ""
        forbidden_reps_str = ""
        if narrative_contract:
            forbidden = getattr(narrative_contract, "forbidden_topic_drift", []) if hasattr(narrative_contract, "forbidden_topic_drift") else narrative_contract.get("forbidden_topic_drift", [])
            forbidden_reps = getattr(narrative_contract, "forbidden_repetitions", []) if hasattr(narrative_contract, "forbidden_repetitions") else narrative_contract.get("forbidden_repetitions", [])
            contract_str = f"NARRATIVE CONTRACT (RÀNG BUỘC CHƯƠNG):\n- CẤM VIẾT CHỆCH HƯỚNG SANG: {forbidden}\n"
            if forbidden_reps:
                forbidden_reps_str = f"- CẤM LẶP LẠI (FORBIDDEN REPETITIONS): {forbidden_reps}\n"

        ledger_str = ""
        if progress_ledger:
            comp_events = getattr(progress_ledger, "completed_events", []) if hasattr(progress_ledger, "completed_events") else progress_ledger.get("completed_events", [])
            rev_info = getattr(progress_ledger, "revealed_information", []) if hasattr(progress_ledger, "revealed_information") else progress_ledger.get("revealed_information", [])
            if comp_events or rev_info:
                ledger_str = f"LOCAL PROGRESS LEDGER (CÁC Ý ĐÃ HOÀN THÀNH Ở SCENE TRƯỚC - KHÔNG LẶP LẠI):\n- Sự kiện đã xong: {comp_events}\n- Thông tin đã tiết lộ: {rev_info}\n"

        global_ledger_str = ""
        if global_ledger:
            g_events = getattr(global_ledger, "completed_events", []) if hasattr(global_ledger, "completed_events") else global_ledger.get("completed_events", [])
            g_claims = getattr(global_ledger, "active_claims", []) if hasattr(global_ledger, "active_claims") else global_ledger.get("active_claims", [])
            global_ledger_str = f"GLOBAL PROGRESS LEDGER (TIẾN TRÌNH TOÀN BỘ STORY - CẤM TÁI KHÁM PHÁ NHƯ MỚI):\n- Sự kiện lịch sử đã xong: {g_events[-5:]}\n- Active Claims (lời phỏng đoán): {g_claims[-5:]}\n"

        return f"""# QWEN2.5 — AUDIO-FIRST SCENE WRITING CONTRACT V2.3 & CANON STATE MACHINE

Bạn không được viết Scene chỉ để tạo văn bản dài.
Mục tiêu duy nhất của Scene là làm câu chuyện TIẾN LÊN.

---

## CANON HIERARCHY & NPC CLAIM ISOLATION RULES
1. CONFIRMED CANON = SỰ THẬT TUYỆT ĐỐI (Engine đã xác nhận).
2. EVIDENCE = BẰNG CHỨNG MẠNH NHƯNG CHƯA PHẢI THỰC TẠI CHẮC CHẮN.
3. CLAIM = LỜI TUYÊN BỐ CỦA NPC / NHÂN VẬT (CHƯA XÁC MINH).
4. RUMOR = TIN ĐỒN TRUYỀN MIỆNG.
5. UNKNOWN = CHƯA RÕ.

⚠️ QUY TẮC BẮT BUỘC VỀ CLAIM:
- Nếu một NPC phát biểu X (ví dụ: "Thanh Vân Quả đến từ Tiên Giới"), đó chỉ là CLAIM.
- Nhân vật chính (Lâm Phàm) chỉ được phép: nghi ngờ, suy ngẫm, tìm bằng chứng.
- NARRATOR VÀ NHÂN VẬT CẤM TỰ YẾU BIẾN CLAIM THÀNH CONFIRMED TRUTH ("Lâm Phàm chắc chắn rằng...", "Sự thật chính là...").

---

## RULE 1 — EVERY SCENE MUST CHANGE THE STORY
Mỗi Scene bắt buộc phải tạo ít nhất 2 trong các thay đổi sau:
- NEW_EVENT
- NEW_INFORMATION
- NEW_EVIDENCE
- NEW_DECISION
- NEW_CONFLICT
- NEW_CHARACTER_STATE
- NEW_RELATIONSHIP_CHANGE
- NEW_CONSEQUENCE

---

## RULE 2 — CAUSAL CHAIN (QUAN HỆ NHÂN QUẢ)
TRIGGER → REACTION → ACTION → DISCOVERY/CONFLICT → DECISION → CONSEQUENCE.
Không viết liệt kê hành động khô khan.

---

## RULE 3 — NO CROSS-CHAPTER REPETITION
Nếu một thông tin hay sự kiện đã xảy ra ở các chương trước hay trong GlobalProgressLedger:
- KHÔNG ĐƯỢC viết như thể nhân vật vừa lần đầu phát hiện.
- KHÔNG ĐƯỢC giới thiệu lại premise cũ như một khám phá mới.

---

## RULE 4 — NO EMOTIONAL LOOP & NO GENERIC PROSE
- Không lặp lại cùng một trạng thái cảm xúc bằng nhiều câu khác nhau.
- Cấm các câu mẫu AI nhàm chán: "Anh nhìn quanh", "Anh cảm thấy xa lạ", "Anh suy nghĩ", "Anh cố giữ bình tĩnh", "Anh không biết phải nói gì".

---

## RULE 5 — DIALOGUE MUST ADVANCE INFORMATION
Mỗi đoạn hội thoại phải làm ít nhất một việc: tiết lộ thông tin mới, thay đổi quan hệ, tạo xung đột, đưa ra quyết định hoặc tạo hậu quả. Không viết hội thoại xã giao.

---

## RULE 6 — SCENE ENDING
Scene BẮT BUỘC kết thúc bằng: thông tin mới, quyết định, hành động, nguy cơ, phát hiện, câu hỏi quan trọng, consequence hoặc HOOK dẫn sang Scene tiếp theo.

---

## RULE 7 — XIANXIA TONE, PRONOUNS & ANTI-DUPLICATION
- Xưng hô Tiên Hiệp chuẩn: Bắt buộc dùng xưng hô 'hắn', 'y', 'tông chủ', 'đệ tử', 'tiền bối', 'vãn bối', 'bản tông'.
- CẤM XƯNG HÔ HIỆN ĐẠI: Tuyệt đối CẤM xưng 'tôi - bạn', CẤM hành vi hiện đại như 'đưa tay ra bắt tay' với Tông chủ.
- CẤM LẶP ĐOẠN VĂN: Tuyệt đối CẤM lặp lại nguyên văn hoặc diễn đạt cùng một đoạn văn 2 lần trong cùng phân cảnh.

---

## MỤC TIÊU PHÂN CẢNH (SCENE GOAL)
- Phân cảnh: Phân cảnh {scene_index} / Chương {chapter_num}
- Mục tiêu Phân cảnh: {scene_goal}
- Cảm xúc chủ đạo: {scene_emotion}
- Xung đột / Trở ngại: {scene_conflict}
- Kết thúc Phân cảnh: {scene_ending}
- Dung lượng mục tiêu: ~{estimated_words} chữ

---

## RÀNG BUỘC CONTRACT & TIẾN TRÌNH LEDGER
{contract_str}
{forbidden_reps_str}
{ledger_str}
{global_ledger_str}

---

## CONTEXT BẮT BUỘC TUÂN THỦ
Chapter Goal: {chapter_goal or 'Tiến triển cốt truyện chương ' + str(chapter_num)}
Tóm tắt Scene trước: {previous_scene_summary or 'Bắt đầu chương'}

{full_context}

---

# ĐẦU RA BẮT BUỘC
Chỉ output duy nhất nội dung văn học của Phân cảnh {scene_index}.
Không output phân tích, JSON, metadata, tiêu đề hay ghi chú.

Bắt đầu viết SCENE {scene_index}:"""





