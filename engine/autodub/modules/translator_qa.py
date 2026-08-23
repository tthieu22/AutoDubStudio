import re
from typing import Dict, List, Any, Optional

class TranslationQaChecker:
    """7-Point Translation Quality Assurance & Semantic QA Engine for Vietnamese Dubbing.
    Pure Detector: Detects issues deterministically without hardcoding text replacements.
    """

    @staticmethod
    def check_segment(
        segment: Dict[str, Any],
        context_prev: str = "",
        context_next: str = "",
        locked_entities: Optional[Dict[str, str]] = None
    ) -> Dict[str, Any]:
        orig = str(segment.get("text") or segment.get("original_text") or "").strip()
        trans = str(segment.get("translated_text") or segment.get("translation") or "").strip()
        seg_id = segment.get("id")

        issues = []

        # 0. Basic Empty Check
        if not trans:
            return {
                "segment_id": seg_id,
                "score": 0,
                "status": "FAIL",
                "issues": [{"type": "EMPTY_TRANSLATION", "severity": "ERROR", "message": "Missing Vietsub translation"}]
            }

        # 1. Meaning Preservation
        is_action_sentence = bool(re.search(r'\b(rubbing|sticks|eating|running|cooking|walking|making|building)\b', orig, re.IGNORECASE))
        is_gibberish_trans = bool(re.search(r'\b(Byé|Dàp-dàp)\b', trans, re.IGNORECASE))
        if is_action_sentence and is_gibberish_trans:
            issues.append({
                "type": "MEANING_PRESERVATION",
                "severity": "ERROR",
                "message": "Semantic Drift Error: Action sentence transformed into meaningless exclamation"
            })

        # 2. Entity Preservation & Relationship Hallucination Check
        if locked_entities:
            for entity_zh, entity_vi in locked_entities.items():
                if entity_zh in orig and entity_vi not in trans:
                    issues.append({
                        "type": "ENTITY_PRESERVATION",
                        "severity": "ERROR",
                        "message": f"Locked Entity violation: '{entity_zh}' should be translated as '{entity_vi}' in Vietsub"
                    })

        # Detect hallucinated extra family/character relationship terms not present in original Chinese
        # (e.g. "Dì", "Chú", "Bác", "Cô", "Pig" added to "爸爸" Father)
        orig_family_terms = re.findall(r'爸爸|妈妈|爷爷|奶奶|叔叔|阿姨|姑姑|舅舅', orig)
        trans_family_hallucinations = re.findall(r'\b(Dì|Chú|Bác|Cô|Thím|Pig|Heo)\b', trans, re.IGNORECASE)
        if trans_family_hallucinations and not any(k in orig for k in ['阿姨', '姑姑', '舅舅', '叔叔', '猪']):
            issues.append({
                "type": "RELATIONSHIP_HALLUCINATION",
                "severity": "ERROR",
                "message": f"Relationship Hallucination Error: Invents character/relationship terms ({', '.join(trans_family_hallucinations)}) not in original Chinese text"
            })

        # 3. Pronoun & Relationship Check
        # Detect unnatural pronouns or un-adapted pronouns
        unadapted_pronouns = re.findall(r'\b(I|you|he|she|they|we|me|him|her)\b', trans, re.IGNORECASE)
        if unadapted_pronouns:
            issues.append({
                "type": "PRONOUN_RELATIONSHIP",
                "severity": "WARNING",
                "message": f"Untranslated English pronoun in Vietsub: {', '.join(unadapted_pronouns)}"
            })

        # 4. Number Preservation (Numbers, time, counts)
        orig_nums = sorted(re.findall(r'\d+', orig))
        trans_nums = sorted(re.findall(r'\d+', trans))
        if orig_nums and orig_nums != trans_nums:
            issues.append({
                "type": "NUMBER_PRESERVATION",
                "severity": "ERROR",
                "message": f"Number mismatch: Original ({', '.join(orig_nums)}) vs Vietsub ({', '.join(trans_nums)})"
            })

        # 5. Hallucination Protection (CJK remnants or invented text)
        if re.search(r'[\u4e00-\u9fff]+', trans):
            issues.append({
                "type": "HALLUCINATION_PROTECTION",
                "severity": "ERROR",
                "message": "Hallucination Error: Chinese characters remaining in Vietnamese output"
            })

        # 6. Natural Vietnamese
        # Check repetitive words ("nào đó nào đó...")
        if re.search(r'(\b[\w\s]{2,20}\b)(?:\s+\1){2,}', trans, re.IGNORECASE):
            issues.append({
                "type": "NATURAL_VIETNAMESE",
                "severity": "WARNING",
                "message": "Unnatural Vietnamese: Repetitive loops detected in Vietsub"
            })

        # 7. Output Integrity (CRITICAL CHECK)
        # Catch AI explanations, English commentary, markdown artifacts, instruction leakage, JSON artifacts
        integrity_issues = []
        
        # Check AI explanations ("This translation maintains...", "Note: ...")
        if re.search(r'\b(this translation|note:|in vietnamese|explanation|translates to)\b', trans, re.IGNORECASE):
            integrity_issues.append("Contains AI explanation / commentary")

        # Check markdown artifacts (**...**, ```...```)
        if re.search(r'\*\*|```|\{|\}', trans):
            integrity_issues.append("Contains markdown or JSON structural artifacts")

        # Check instruction leakage ("System:", "Rules:", "Output:")
        if re.search(r'\b(system:|rules:|instruction|prompt:)\b', trans, re.IGNORECASE):
            integrity_issues.append("Contains system instruction leakage")

        # Check multiple translations provided on separate lines or quotes
        if "\n" in trans or re.search(r'Option 1|Option 2|Bản 1|Bản 2', trans, re.IGNORECASE):
            integrity_issues.append("Contains multiple translation options instead of single output")

        if integrity_issues:
            issues.append({
                "type": "OUTPUT_INTEGRITY",
                "severity": "ERROR",
                "message": f"Output Integrity Violation: {'; '.join(integrity_issues)}"
            })

        # Score calculation across 7 dimensions
        score = 100
        for issue in issues:
            if issue["severity"] == "ERROR":
                score -= 30
            elif issue["severity"] == "WARNING":
                score -= 15
        score = max(0, score)

        status = "PASS"
        if any(i["severity"] == "ERROR" for i in issues):
            status = "FAIL"
        elif issues or score < 85:
            status = "REVIEW"

        return {
            "segment_id": seg_id,
            "score": score,
            "status": status,
            "issues": issues
        }

    @classmethod
    def check_project(cls, segments: List[Dict[str, Any]], locked_entities: Optional[Dict[str, str]] = None) -> Dict[str, Any]:
        results = [cls.check_segment(s, locked_entities=locked_entities) for s in segments]
        total_score = sum(r["score"] for r in results)
        overall_score = round(total_score / max(1, len(segments)))

        flagged_count = sum(1 for r in results if r["status"] != "PASS")
        error_count = sum(1 for r in results if r["status"] == "FAIL")
        warning_count = sum(1 for r in results if r["status"] == "REVIEW")

        return {
            "overall_score": overall_score,
            "flagged_count": flagged_count,
            "error_count": error_count,
            "warning_count": warning_count,
            "results": results
        }
