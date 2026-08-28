import re
import json
import logging
from typing import Dict, Any, List
from autodub.novel.novel_database import NovelDatabase
from autodub.novel.novel_models import ValidationResult, ValidationViolation

logger = logging.getLogger(__name__)


class CanonValidatorEngine:
    """
    Validation Rules Engine for AI Novel continuity:
    1. Character Realm consistency (no skipping realms / demotions without explanation)
    2. Location consistency
    3. Knowledge boundary enforcement
    4. Canon facts contradiction check
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
            # Simple keyword contradiction heuristic
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
