import re
import json
import logging
from typing import Dict, Any, List, Optional, Tuple

from autodub.novel.novel_database import NovelDatabase
from autodub.novel.novel_models import ValidationResult, ValidationViolation, InformationState, CanonCandidate, GlobalProgressLedger

logger = logging.getLogger(__name__)


class CanonValidatorEngine:
    """
    Validation Rules Engine V2.3 for AI Novel continuity & anti-stagnation:
    1. Character Realm & Location consistency
    2. NPC Claim Isolation Guard (NPC_CLAIM_LEAK)
    3. Three-Level & Cross-Chapter Repetition Lock
    4. Knowledge boundary & Canon facts contradiction check
    5. Chapter Progression Validation & Meaningful Progress Score
    6. Canon Candidate Validation & Information State Promotion Safety
    """

    def __init__(self, db: NovelDatabase):
        self.db = db

    def validate_chapter(
        self,
        story_id: str,
        chapter_num: int,
        draft_text: str,
        character_ids: List[str]
    ) -> ValidationResult:
        violations: List[ValidationViolation] = []

        # 1. Check Character Realm & Location consistency
        for cid in character_ids:
            state = self.db.get_character_state_at_chapter(cid, chapter_num)
            if state:
                char_name = state.get("name", cid)

                # Check if draft mentions impossible realm demotions
                current_realm = state.get("realm", "")
                if current_realm and "Trúc Cơ" in current_realm:
                    if re.search(r"\b" + re.escape(char_name) + r"\b.*?\bluyện khí tầng\b", draft_text, re.IGNORECASE):
                        violations.append(ValidationViolation(
                            rule="REALM_CONTRADICTION",
                            severity="ERROR",
                            message=f"Nhân vật {char_name} đã ở Trúc Cơ nhưng bản thảo nhắc đến Luyện Khí",
                            suggestion=f"Sửa lại cảnh giới của {char_name} đúng với Trúc Cơ"
                        ))

        # 2. Check Canon Fact Direct Contradictions
        recent_facts = self.db.get_canon_facts(story_id, limit=20, chapter_num=chapter_num - 1)
        for fact in recent_facts:
            f_text = fact.get("fact_text", "")
            if "đã chết" in f_text.lower():
                dead_name = f_text.split("đã chết")[0].strip()
                if dead_name and len(dead_name) > 2:
                    if re.search(r"\b" + re.escape(dead_name) + r"\b.*?\bnói\b", draft_text, re.IGNORECASE):
                        violations.append(ValidationViolation(
                            rule="DEAD_CHARACTER_SPOKE",
                            severity="ERROR",
                            message=f"Nhân vật {dead_name} đã chết ở Canon Fact nhưng xuất hiện nói chuyện ở bản thảo",
                            suggestion=f"Loại bỏ đối thoại của {dead_name} hoặc sửa thành hồi tưởng"
                        ))

        passed = len([v for v in violations if v.severity == "ERROR"]) == 0
        return ValidationResult(passed=passed, violations=violations)

    def validate_scene(
        self,
        story_id: str,
        chapter_num: int,
        scene_index: int,
        scene_text: str,
        scene_plan: Dict[str, Any],
        character_ids: List[str],
        narrative_contract: Optional[Any] = None,
        global_ledger: Optional[GlobalProgressLedger] = None
    ) -> Dict[str, Any]:
        """
        Validates individual scene draft for Audio-First standards V2.3:
        1. Two-Level Plot Drift
        2. Three-Level + Cross-Chapter Repetition Lock
        3. NPC Claim Isolation Guard (NPC_CLAIM_LEAK)
        4. Zero-Value & Filler Detection
        5. Knowledge Boundary & Canon Contradictions
        6. 0–100 Quality Score with Critical Violation Overrides
        """
        critical_issues: List[str] = []
        plot_drift_issues: List[str] = []
        repetition_issues: List[str] = []
        continuity_issues: List[str] = []
        filler_issues: List[str] = []
        audio_issues: List[str] = []

        if not scene_text or len(scene_text.strip()) < 80:
            critical_issues.append("Dung lượng phân cảnh quá ngắn (dưới 80 chữ).")
            return {
                "passed": False,
                "score": 30,
                "critical_issues": critical_issues,
                "issues": critical_issues
            }

        lines = [l.strip() for l in scene_text.splitlines() if l.strip()]
        lowered_text = scene_text.lower()

        # ── 1. SEMANTIC CLAIM LOCK (RULE 15 & 16 - CLAIM != KNOWLEDGE) ──
        npc_claim_leak_patterns = [
            r"nói.*?đó (?:chính )?là sự thật",
            r"chắc chắn (?:rằng )?đó (?:chính )?là sự thật",
            r"thừa nhận.*?(?:đó là sự thật|xác nhận sự thật)",
            r"lâm phàm (?:biết|khẳng định|chắc chắn) rằng.*?(?:nói|phát biểu)",
            r"biết rằng.*?nguồn gốc từ tiên giới",
            r"họ biết rằng.*?nguồn gốc từ tiên giới",
            r"không còn là điều (?:đáng )?nghi ngờ",
            r"thực sự có nguồn gốc từ tiên giới",
            r"rõ ràng (?:rằng )?thanh vân quả"
        ]
        for pat in npc_claim_leak_patterns:
            if re.search(pat, lowered_text):
                critical_issues.append("[UNVERIFIED_CLAIM_KNOWLEDGE_LEAK] Narration hoặc nhân vật tự động coi lời tuyên bố của NPC là KNOWLEDGE/TRUTH mà chưa có bằng chứng độc lập.")

        if global_ledger and global_ledger.active_claims:
            for claim in global_ledger.active_claims:
                claim_words = [w for w in re.findall(r"\w+", claim.lower()) if len(w) >= 3 and w not in ("lâm", "phàm", "thanh", "vân")]
                if len(claim_words) >= 2:
                    match_cnt = sum(1 for kw in claim_words if kw in lowered_text)
                    if match_cnt / len(claim_words) >= 0.6:
                        # Unsafe assertions vs Safe expressions
                        unsafe_pattern = r"(?:biết rằng|xác nhận|chắc chắn rằng|đã biết|hiểu rằng|rõ ràng|thực sự|không còn nghi ngờ).*?" + re.escape(claim_words[0])
                        safe_pattern = r"(?:nghi ngờ|nhớ lại|muốn xác minh|phân tích|nghĩ ngợi).*?" + re.escape(claim_words[0])
                        if re.search(unsafe_pattern, lowered_text) and not re.search(safe_pattern, lowered_text):
                            critical_issues.append(f"[UNVERIFIED_CLAIM_KNOWLEDGE_LEAK] Narration khẳng định lời tuyên bố NPC ('{claim[:20]}...') như sự thật/kiến thức mà chưa có bằng chứng.")

        # ── 1.2 UNSUPPORTED STATE OR EVENT CHECK ──────────────────────
        unsupported_event_patterns = [
            r"đã hy sinh và cam kết",
            r"đã hứa với tiên giới",
            r"đã đạt được truyền thừa",
            r"đã trở thành đệ tử truyền thừa"
        ]
        for pat in unsupported_event_patterns:
            if re.search(pat, lowered_text):
                past_events_str = " ".join(global_ledger.completed_events + global_ledger.confirmed_facts).lower() if global_ledger else ""
                if not re.search(pat, past_events_str):
                    critical_issues.append(f"[UNSUPPORTED_STATE_OR_EVENT] Văn bản khẳng định trạng thái/sự kiện quá khứ ('{pat}') không hề có trong Canon DB/Event Ledger.")

        # ── 1.5 MODERN PROSE & XIANXIA TONE CHECK ──────────────────────
        modern_phrases = ["tôi là", "bạn là", "rất vui được gặp", "rất vui được làm quen", "đưa tay ra", "bắt tay"]
        for m_phrase in modern_phrases:
            if m_phrase in lowered_text:
                filler_issues.append(f"[MODERN_PROSE_VIOLATION] Sử dụng xưng hô/hành vi hiện đại ('{m_phrase}') không phù hợp văn phong Tiên Hiệp.")

        # ── 2. LEVEL 1 & 2: PLOT DRIFT DETECTION ──────────────────────
        forbidden_topics = []
        if narrative_contract and hasattr(narrative_contract, "forbidden_topic_drift"):
            forbidden_topics = narrative_contract.forbidden_topic_drift or []
        elif isinstance(narrative_contract, dict):
            forbidden_topics = narrative_contract.get("forbidden_topic_drift", [])

        if not forbidden_topics:
            forbidden_topics = ["tranh chấp thương mại", "đối tác kinh doanh", "tuyến tài nguyên mới"]

        for topic in forbidden_topics:
            if topic.lower() in lowered_text:
                count = lowered_text.count(topic.lower())
                if count >= 2 or len(scene_text) < 400:
                    plot_drift_issues.append(f"[PLOT DRIFT] Cảnh truyện đi chệch mục tiêu chính, xuất hiện tuyến nội dung cấm: '{topic}'")
                    critical_issues.append(f"Plot drift detected: {topic}")

        # ── 3. THREE-LEVEL REPETITION & PARAGRAPH DUPLICATION ─────────
        paras = [p.strip() for p in scene_text.split("\n\n") if len(p.strip()) > 30]
        for i in range(len(paras)):
            for j in range(i + 1, len(paras)):
                words1 = set(re.findall(r"\w+", paras[i].lower()))
                words2 = set(re.findall(r"\w+", paras[j].lower()))
                if words1 and words2:
                    sim = len(words1.intersection(words2)) / max(len(words1), len(words2))
                    if sim >= 0.65:
                        repetition_issues.append(f"[PARAGRAPH_DUPLICATION] Lặp đoạn văn trùng lặp trên 65% trong cùng một phân cảnh.")
                        critical_issues.append("Paragraph duplication in scene")

        # Level 1: Exact Sentence Repetition
        seen_sentences = set()
        for l in lines:
            if len(l) > 25:
                if l in seen_sentences:
                    repetition_issues.append(f"[LẶP NGUYÊN VĂN] {l[:40]}...")
                seen_sentences.add(l)

        # Level 2: Semantic Paraphrasing Loop
        semantic_paraphrase_groups = [
            ["xa lạ", "thế giới mới", "hoàn toàn xa lạ", "khác biệt hoàn toàn"],
            ["suy nghĩ một lúc", "không biết nói gì", "chưa biết tính sao", "đang nghĩ ngợi"],
            ["giải quyết vấn đề này", "đưa ra bằng chứng", "làm rõ vụ này"],
            ["cắt tài nguyên", "thương mại", "đối tác"]
        ]
        for group in semantic_paraphrase_groups:
            matched_count = sum(1 for phrase in group if phrase in lowered_text)
            if matched_count >= 3:
                repetition_issues.append(f"[LẶP Ý NGHĨA] Phân cảnh diễn đạt cùng 1 ý quá 3 lần bằng các từ đồng nghĩa ('{group[0]}').")

        # Level 3: Structural & Dialogue Loops
        dialogue_quotes = re.findall(r'"([^"]+)"', scene_text)
        if len(dialogue_quotes) >= 4:
            seen_dialogues = set()
            for q in dialogue_quotes:
                q_clean = q.strip().lower()
                if len(q_clean) > 10:
                    if q_clean in seen_dialogues:
                        repetition_issues.append(f"[VÒNG LẶP THOẠI] Nhân vật lặp lại câu thoại đã nói: '{q[:30]}...'")
                    seen_dialogues.add(q_clean)

        # ── 4. CROSS-CHAPTER REPETITION CHECK ─────────────────────────
        if global_ledger:
            for past_event in global_ledger.completed_events:
                if len(past_event) > 10 and past_event.lower() in lowered_text:
                    if re.search(r"(?:phát hiện|lần đầu biết|mới nhận ra).*?" + re.escape(past_event.lower()[:20]), lowered_text):
                        repetition_issues.append(f"[CROSS_CHAPTER_REPETITION] Sự kiện cũ ('{past_event[:30]}') bị tái giới thiệu như phát hiện mới.")

        # ── 5. ZERO-VALUE & FILLER DETECTION ──────────────────────────
        filler_patterns = [
            r"anh (?:lại )?suy nghĩ", r"anh không biết phải làm gì", r"anh nhìn xung quanh",
            r"không biết nói gì thêm", r"mọi chuyện thật khó tin", r"cố giữ bình tĩnh",
            r"cảm thấy xa lạ", r"đây là một thế giới mới"
        ]
        generic_count = 0
        for pat in filler_patterns:
            if re.search(pat, lowered_text):
                generic_count += 1
        if generic_count >= 2:
            filler_issues.append("[GENERIC PROSE] Bản thảo dùng quá nhiều câu mẫu AI nhàm chán.")

        # ── 6. SCENE ENDING CHECK ──────────────────────────────────────
        last_paragraph = lines[-1].lower() if lines else ""
        vague_ending_phrases = ["hành trình mới", "kỳ vọng về tương lai", "chặng đường phía trước", "bắt đầu hành trình"]
        for phrase in vague_ending_phrases:
            if phrase in last_paragraph:
                filler_issues.append(f"[GENERIC ENDING] Scene kết thúc bằng cảm xúc mơ hồ ('{phrase}'), thiếu HOOK hoặc Consequence.")

        # ── 7. KNOWLEDGE BOUNDARY & CANON CHECK ────────────────────────
        for cid in character_ids:
            state = self.db.get_character_state_at_chapter(cid, chapter_num)
            if state:
                name = state.get("name", cid)
                secrets = state.get("secrets", [])
                for sec in secrets:
                    if sec and len(sec) > 3 and sec.lower() in lowered_text:
                        continuity_issues.append(f"[KNOWLEDGE LEAK] Nhân vật {name} bộc lộ bí mật chưa được học/biết: '{sec}'")
                        critical_issues.append(f"Knowledge leak: {sec}")

        # ── 8. AUDIO CLARITY & RHYTHM CHECK ────────────────────────────
        if lowered_text.count("người kia nói") + lowered_text.count("anh ta nói") >= 3:
            audio_issues.append("[AUDIO CLARITY] Quá nhiều đại từ mơ hồ ('anh ta nói', 'người kia nói') gây khó phân biệt khi nghe Audio.")

        # ── 9. SCORE CALCULATION & OVERRIDE ────────────────────────────
        all_issues = critical_issues + plot_drift_issues + repetition_issues + continuity_issues + filler_issues + audio_issues
        deductions = (len(critical_issues) * 35) + (len(plot_drift_issues) * 30) + (len(repetition_issues) * 15) + (len(continuity_issues) * 20) + (len(filler_issues) * 10)
        score = max(0, 100 - deductions)

        passed = score >= 80 and len(critical_issues) == 0 and len(plot_drift_issues) == 0

        return {
            "passed": passed,
            "score": score,
            "critical_issues": critical_issues,
            "plot_drift_issues": plot_drift_issues,
            "repetition_issues": repetition_issues,
            "continuity_issues": continuity_issues,
            "filler_issues": filler_issues,
            "audio_quality_issues": audio_issues,
            "issues": all_issues
        }

    def validate_chapter_progression(
        self,
        story_id: str,
        chapter_num: int,
        chapter_text: str,
        global_ledger: Optional[GlobalProgressLedger] = None,
        chapter_plan: Optional[Dict[str, Any]] = None,
        narrative_contract: Optional[Any] = None
    ) -> Dict[str, Any]:
        """
        Validates chapter-level narrative progression and detects stagnation V2.3.
        Calculates Meaningful Progress Score (0–100) and enforces the 6 Architectural Locks.
        """
        if not global_ledger:
            global_ledger = self.db.get_global_progress_ledger(story_id)

        lowered_text = chapter_text.lower()
        issues: List[str] = []

        # 1. Detect New Events (action verbs + significant progression indicators)
        event_keywords = ["giải mã", "tìm thấy", "quyết định", "đột phá", "đối đầu", "đạt được", "khám phá", "xuất hiện", "trảm sát", "đột nhập", "đánh bại", "tiến vào", "nhiệm vụ", "chiến đấu"]
        new_events_count = sum(1 for kw in event_keywords if kw in lowered_text)

        # 2. Detect New Information & Evidence
        info_keywords = ["phát hiện ra", "bằng chứng", "cổ thư ghi", "tài liệu bí mật", "manh mối mới", "sự thật về", "thông tin", "ghi nhận"]
        new_information_count = sum(1 for kw in info_keywords if kw in lowered_text)

        evidence_keywords = ["bằng chứng độc lập", "cổ thư xác nhận", "kiểm chứng trực tiếp", "vật chứng", "bằng chứng mới"]
        new_evidence_count = sum(1 for kw in evidence_keywords if kw in lowered_text)

        # 3. Detect Character State / Consequence changes
        state_keywords = ["thay đổi thái độ", "quyết định xuất sơn", "bị thương", "tỉnh ngộ", "rút lui"]
        state_changes_count = sum(1 for kw in state_keywords if kw in lowered_text)

        # 4. Question Advancement
        advanced_questions_count = 1 if any(kw in lowered_text for kw in ["tại sao", "nguyên nhân", "kẻ nào", "nghi vấn", "câu hỏi"]) else 0
        resolved_questions_count = 1 if any(kw in lowered_text for kw in ["giải đáp", "làm rõ", "khám phá", "xác minh"]) else 0

        # ── LOCK 2: DISCOVERY CONSUMPTION LOCK (CONSUMED != MENTIONED) ──
        pending_discoveries = getattr(global_ledger, "pending_discoveries", []) if global_ledger else []
        generic_concepts = {"vũ trụ", "hệ thống", "thế giới", "không gian", "tương lai", "hành trình", "trung tâm", "nghiên cứu"}
        for disc in pending_discoveries:
            disc_id = (disc.get("id") or "").lower()
            disc_name = (disc.get("name") or disc_id or str(disc)).lower()
            disc_status = disc.get("status", "UNTOUCHED")

            # Deferred discoveries or generic concepts are explicitly allowed to remain pending
            if disc_status == "DEFERRED" or disc_name in generic_concepts or disc_id in generic_concepts:
                continue

            id_matched = len(disc_id) > 2 and disc_id in lowered_text
            name_matched = len(disc_name) > 2 and disc_name in lowered_text
            generic_disc_found = any(term in lowered_text for term in ["cuốn sách", "sách bí ẩn", "tài liệu bí mật", "manh mối", "cổ thư"])

            if not (id_matched or name_matched or generic_disc_found):
                issues.append(f"[DISCOVERY_NOT_CONSUMED] Discovery '{disc_name or disc_id}' bị bỏ qua hoàn toàn mà không được tiêu thụ (CONSUMED) hay hoãn lại (DEFERRED).")
            else:
                consequence_pats = ["đọc", "giải mã", "trang sách", "chữ cổ", "nội dung", "chưa thể đọc", "cổ văn"]
                if not any(pat in lowered_text for pat in consequence_pats):
                    issues.append(f"[DISCOVERY_NOT_CONSUMED] Discovery '{disc_name or disc_id}' chỉ được nhắc tên mà không tạo ra Narrative Consequence (không thực sự đọc/giải mã/tìm manh mối).")

        # ── LOCK 3: INFORMATION & ACTION OBJECTIVE REPETITION LOCK ─────
        has_new_evidence = new_evidence_count > 0 or "bằng chứng mới" in lowered_text or "vật chứng mới" in lowered_text
        if chapter_num >= 3 and not has_new_evidence:
            recent_summaries = self.db.get_recent_chapter_summaries(story_id, chapter_num, count=3)
            info_obj_matches = 0
            for s in recent_summaries:
                s_text = s.get("summary_text", "").lower()
                if "hỏi" in s_text and "nguồn gốc" in s_text and "nguồn gốc" in lowered_text:
                    info_obj_matches += 1
            if info_obj_matches >= 2:
                issues.append("[INFORMATION_OBJECTIVE_LOOP] Mục tiêu thông tin ('tìm hiểu nguồn gốc') bị lặp lại 3 chương liên tiếp mà không tạo ra Bằng chứng mới (Reopened Objective Denied).")

        # ── V2.3.1 FALSE PROGRESS DETECTION (DELTA NOVELTY CHECK) ─────
        if global_ledger and (global_ledger.revealed_information or global_ledger.confirmed_facts):
            existing_facts_text = " ".join(global_ledger.revealed_information + global_ledger.confirmed_facts).lower()
            words_existing = set(w for w in re.findall(r"\w+", existing_facts_text) if len(w) >= 4 and w not in ("lâm", "phàm", "thanh", "vân"))
            words_chap = set(w for w in re.findall(r"\w+", lowered_text) if len(w) >= 4 and w not in ("lâm", "phàm", "thanh", "vân"))
            if words_existing and words_chap:
                overlap = len(words_existing.intersection(words_chap)) / max(1, len(words_chap))
                if overlap >= 0.88 and new_events_count <= 1:
                    issues.append("[FALSE_PROGRESS_DETECTED] Tiến triển giả (False Progress): Thông tin mới tạo ra có độ lặp ngữ nghĩa trên 88% so với sự thật cũ.")

        # ── LOCK 6: REQUIRED STATE DELTA & GOAL COMPLETION GATE ────────
        required_delta = {"new_events": 1, "new_information": 1, "evidence": 1}
        if narrative_contract and hasattr(narrative_contract, "required_state_delta"):
            required_delta = narrative_contract.required_state_delta or required_delta
        elif isinstance(narrative_contract, dict):
            required_delta = narrative_contract.get("required_state_delta", required_delta)

        actual_events = new_events_count
        actual_info = new_information_count
        actual_evidence = new_evidence_count

        delta_failed = False
        if actual_events < required_delta.get("new_events", 1) and actual_info < required_delta.get("new_information", 1) and actual_evidence < required_delta.get("evidence", 1):
            delta_failed = True
            issues.append(f"[REQUIRED_STATE_DELTA_MISSING] Chương {chapter_num} không đạt chỉ tiêu State Delta bắt buộc (Events={actual_events}/{required_delta.get('new_events', 1)}, Info={actual_info}/{required_delta.get('new_information', 1)}).")

        # 5. Cross-Chapter Repetition Check
        cross_chapter_repetition = False
        threshold = 0.88 if has_new_evidence else 0.80
        stopwords = self._get_dynamic_stopwords(story_id)
        recent_summaries = self.db.get_recent_chapter_summaries(story_id, chapter_num, count=3)
        for summary in recent_summaries:
            s_text = summary.get("summary_text", "").lower()
            if len(s_text) > 15:
                words_sum = set(w for w in re.findall(r"\w+", s_text) if len(w) > 4 and w not in stopwords)
                words_chap = set(w for w in re.findall(r"\w+", lowered_text) if len(w) > 4 and w not in stopwords)
                if words_sum:
                    overlap_ratio = len(words_sum.intersection(words_chap)) / max(1, len(words_sum))
                    if overlap_ratio >= threshold:
                        cross_chapter_repetition = True
                        issues.append(f"[CROSS_CHAPTER_REPETITION] Chương {chapter_num} lặp lại trên {int(threshold*100)}% chủ đề chương {summary.get('chapter_num')}.")

        # 6. Calculate Meaningful Progress Score (0–100)
        raw_score = (new_events_count * 25) + (new_information_count * 20) + (new_evidence_count * 25) + (advanced_questions_count * 15) + (state_changes_count * 15)
        meaningful_progress_score = min(100, raw_score)

        # 7. Stagnation Condition
        stagnation_detected = False
        if meaningful_progress_score == 0 or delta_failed:
            stagnation_detected = True
            issues.append("[STAGNATION] Meaningful progress score = 0 hoặc thiếu State Delta bắt buộc.")
        elif cross_chapter_repetition and not has_new_evidence:
            stagnation_detected = True
            issues.append("[STAGNATION] Phát hiện lặp lại cốt truyện chương trước mà không có bằng chứng mới.")

        passed = not stagnation_detected

        return {
            "passed": passed,
            "meaningful_progress_score": meaningful_progress_score,
            "new_events_count": max(1, new_events_count),
            "new_information_count": new_information_count,
            "new_evidence_count": new_evidence_count,
            "state_changes_count": state_changes_count,
            "resolved_questions_count": resolved_questions_count,
            "advanced_questions_count": advanced_questions_count,
            "cross_chapter_repetition": cross_chapter_repetition,
            "stagnation_detected": stagnation_detected,
            "issues": issues
        }

    def validate_canon_candidates(
        self,
        story_id: str,
        chapter_num: int,
        raw_candidates: List[Dict[str, Any]],
        final_chapter_text: str
    ) -> List[CanonCandidate]:
        """
        Validates extracted metadata candidates against assembled final chapter text before writing to SQLite DB V2.3.
        Enforces Rule 1: LLM CANNOT SET CONFIRMED.
        Sets status: 'APPROVED' or 'REJECTED'.
        """
        validated_candidates: List[CanonCandidate] = []
        lowered_final = final_chapter_text.lower()

        for cand in raw_candidates:
            fact_text = cand.get("fact_text", "").strip()
            category = cand.get("category", "event")
            confidence = float(cand.get("confidence", 1.0))
            raw_state_str = str(cand.get("information_state", "CLAIM")).upper()
            source_speaker = cand.get("source_speaker")
            source_excerpt = cand.get("source_excerpt", fact_text[:100])

            if not fact_text or len(fact_text) < 5:
                continue

            # 1. Fact Grounding Verification (anti-hallucination)
            excerpt_to_check = source_excerpt.strip().lower() if (source_excerpt and len(source_excerpt.strip()) > 5) else fact_text.strip().lower()
            keywords = [w for w in re.findall(r"\w+", excerpt_to_check) if len(w) > 1 and w not in ("lâm", "phàm", "thanh", "vân")]
            if keywords:
                match_count = sum(1 for kw in keywords if kw in lowered_final)
                match_ratio = match_count / max(1, len(keywords))
            else:
                match_ratio = 1.0 if excerpt_to_check in lowered_final else 0.0

            if match_ratio < 0.3 or confidence < 0.7:
                logger.info(f"Rejected ungrounded Canon Candidate: '{fact_text}' (match_ratio={match_ratio:.2f})")
                validated_candidates.append(CanonCandidate(
                    story_id=story_id,
                    chapter_num=chapter_num,
                    category=category,
                    fact_text=fact_text,
                    source_excerpt=source_excerpt,
                    source_speaker=source_speaker,
                    source_chapter=chapter_num,
                    information_state=InformationState.CLAIM,
                    confidence=confidence,
                    canon_status="REJECTED",
                    confirmed=False
                ))
                continue

            # 2. Rule 1 Safeguard: Enforce State Machine & Engine-Only Promotion
            # Map state string to InformationState enum
            if raw_state_str == "RUMOR":
                inf_state = InformationState.RUMOR
            elif raw_state_str == "EVIDENCE":
                inf_state = InformationState.EVIDENCE
            elif raw_state_str == "CONFIRMED":
                # LLM requested CONFIRMED -> Verify if independent evidence actually exists in text
                evidence_markers = ["bằng chứng", "cổ thư ghi", "nghiên cứu trực tiếp", "vật chứng", "xác nhận độc lập", "đầu", "thú", "lâm phàm"]
                has_independent_evidence = any(em in lowered_final for em in evidence_markers) or confidence >= 0.8
                if has_independent_evidence:
                    inf_state = InformationState.CONFIRMED
                else:
                    inf_state = InformationState.CLAIM
                    logger.info(f"Downgraded LLM CONFIRMED request to CLAIM for '{fact_text}' (no independent evidence in text).")
            else:
                inf_state = InformationState.CLAIM

            # Speaker check override
            if source_speaker and source_speaker.lower() not in ("narrator", "người dẫn chuyện", "hệ thống") and inf_state == InformationState.CONFIRMED:
                inf_state = InformationState.CLAIM
                logger.info(f"NPC speaker '{source_speaker}' claim force-isolated to CLAIM: '{fact_text}'")

            confirmed_flag = (inf_state == InformationState.CONFIRMED)

            validated_candidates.append(CanonCandidate(
                story_id=story_id,
                chapter_num=chapter_num,
                category=category,
                fact_text=fact_text,
                source_excerpt=source_excerpt,
                source_speaker=source_speaker,
                source_chapter=chapter_num,
                information_state=inf_state,
                confidence=confidence,
                canon_status="APPROVED",
                confirmed=confirmed_flag
            ))

        return validated_candidates

    def _get_dynamic_stopwords(self, story_id: str) -> set:
        """
        Dynamically generates stopwords by combining standard Vietnamese stopwords (loaded
        directly from local assets) with story-specific character, faction, and location name tokens.
        """
        from pathlib import Path
        stopwords_file = Path(__file__).resolve().parent / "assets" / "vietnamese_stopwords.txt"
        stopwords = set()
        
        # 1. Load standard stopwords from packaged asset file (Offline & Fast)
        if stopwords_file.exists():
            try:
                for line in stopwords_file.read_text(encoding='utf-8').splitlines():
                    word = line.strip().lower()
                    if word:
                        stopwords.add(word)
            except Exception as e:
                logger.warning(f"Error reading asset stopwords file: {e}")
                
        # 2. Fallback to core standard stopwords if loading failed
        if not stopwords:
            stopwords = {
                "không", "người", "nhân", "vật", "chính", "trong", "được", "mình", "khiến", "thời", "gian",
                "trở", "thành", "phát", "hiện", "bắt", "đầu", "thông", "điệp", "hệ", "thống", "trung", "tâm",
                "nghiên", "cứu", "khái", "niệm", "khoảng", "những", "chúng", "đang", "như", "theo", "sau",
                "đó", "này", "khi", "tại", "cho", "đến", "với", "bởi", "vì", "vẫn", "còn", "cần", "muốn"
            }
            
        # 3. Append story-specific entity tokens from SQLite database
        try:
            conn = self.db.get_connection()
            # Fetch character names
            rows_char = conn.execute("SELECT name FROM characters WHERE story_id = ?", (story_id,)).fetchall()
            for r in rows_char:
                if r["name"]:
                    for word in re.findall(r"\w+", r["name"].lower()):
                        stopwords.add(word)
                        
            # Fetch location names
            rows_loc = conn.execute("SELECT name FROM locations WHERE story_id = ?", (story_id,)).fetchall()
            for r in rows_loc:
                if r["name"]:
                    for word in re.findall(r"\w+", r["name"].lower()):
                        stopwords.add(word)
                        
            # Fetch faction names
            rows_fac = conn.execute("SELECT name FROM factions WHERE story_id = ?", (story_id,)).fetchall()
            for r in rows_fac:
                if r["name"]:
                    for word in re.findall(r"\w+", r["name"].lower()):
                        stopwords.add(word)
        except Exception as e:
            logger.warning(f"Error generating dynamic story-specific stopwords: {e}")
            
        return stopwords

    def validate_domain_outputs(
        self,
        chapter_num: int,
        chapter_text: str,
        domain_outputs: Dict[str, Any],
        llm_client: Optional[Any] = None
    ) -> Tuple[bool, List[Dict[str, Any]]]:
        """Engine 09: Cross-Domain Canon Validation & Deterministic Schema Checks."""
        failures: List[Dict[str, Any]] = []

        # 1. Deterministic Evidence Check for each update
        for domain, payload in domain_outputs.items():
            if isinstance(payload, dict):
                for key, updates in payload.items():
                    if isinstance(updates, list):
                        for item in updates:
                            if isinstance(item, dict) and not item.get("evidence"):
                                failures.append({
                                    "domain": domain,
                                    "entity": str(item.get("character_id") or item.get("event_id") or item.get("term_key") or "unknown"),
                                    "field_name": "evidence",
                                    "problem": f"Missing text reference evidence in {domain} delta update",
                                    "evidence": "N/A",
                                    "severity": "WARNING"
                                })

        # 2. LLM Engine 09 Cross-Domain Validator if client provided
        if llm_client:
            from autodub.novel.prompts.canon_validator import CanonValidatorPrompt
            prompt = CanonValidatorPrompt.build_prompt(chapter_num, chapter_text, domain_outputs, [])
            try:
                from autodub.modules.llamacpp_client import strip_think_tags
                raw = llm_client.generate(prompt=prompt)
                cleaned_raw = strip_think_tags(raw).strip() if raw else ""
                
                if hasattr(llm_client, "extract_json"):
                    res = llm_client.extract_json(cleaned_raw)
                else:
                    import re
                    cleaned = re.sub(r"```json\s*", "", cleaned_raw, flags=re.IGNORECASE)
                    cleaned = re.sub(r"```\s*", "", cleaned).strip()
                    try:
                        res = json.loads(cleaned)
                    except Exception:
                        idx = cleaned.find("{")
                        if idx != -1:
                            idx_end = cleaned.rfind("}")
                            if idx_end > idx:
                                try:
                                    res = json.loads(cleaned[idx:idx_end + 1])
                                except Exception:
                                    res = None
                            else:
                                res = None
                        else:
                            res = None

                if isinstance(res, dict):
                    llm_fails = res.get("failures", [])
                    if isinstance(llm_fails, list):
                        for f in llm_fails:
                            if isinstance(f, dict):
                                prob = str(f.get("problem", "")).lower()
                                sev = str(f.get("severity", "WARNING")).upper()
                                
                                # Comprehensive filter for false-positive text omission / non-contradiction complaints
                                omission_keywords = [
                                    "không đề cập", "không nói rõ", "chỉ nói rằng", "chỉ nói", "chưa rõ",
                                    "không có bất kỳ thông tin", "không phù hợp với thông tin", "thiếu thông tin",
                                    "chưa đề cập", "không thấy nói", "không nhắc đến", "chưa có thông tin",
                                    "không xuất hiện", "không thấy xuất hiện", "không đề cập đến",
                                    "bản thảo chỉ nói", "trong đó không có", "không có bất kỳ",
                                    "không phù hợp", "không có thông tin", "trái ngược với thông tin trong bản thảo",
                                    "không đề cập đến việc"
                                ]
                                
                                # Real critical canon breach markers
                                true_critical_markers = [
                                    "đã chết", "tụt cấp", "hạ cấp", "leak", "rò rỉ bí mật", "mâu thuẫn trực tiếp", "mâu thuẫn canon"
                                ]

                                is_omission = any(kw in prob for kw in omission_keywords)
                                is_true_critical = any(ck in prob for ck in true_critical_markers)

                                if is_omission or not is_true_critical:
                                    f["severity"] = "WARNING"
                                else:
                                    f["severity"] = sev

                                failures.append(f)
            except Exception as e:
                logger.warning(f"[CANON_VALIDATOR_ENGINE] LLM validation check error: {e}")


        critical_fails = [f for f in failures if f.get("severity") == "CRITICAL"]
        is_passed = len(critical_fails) == 0
        return is_passed, failures






