import re
import json
import logging
from typing import Dict, Any, Optional, List
from autodub.modules.ollama_client import OllamaClient
from autodub.modules.translator_qa import TranslationQaChecker
from autodub.modules.output_sanitizer import TranslationOutputSanitizer
from autodub.modules.structured_parser import StructuredParser

logger = logging.getLogger("autodub")

class TranslationRepairService:
    """Dynamic LLM AI Translation Repair Service (Strict 1-Pass Limit).
    Receives original_text, current_translated_text, QA issues, context, and locked entity memory.
    Executes EXACTLY 1 AI Repair attempt, sanitizes format, evaluates QA #2, and falls back to HUMAN_REVIEW if QA #2 fails.
    """

    def __init__(self, ollama_client: Optional[OllamaClient] = None, model_name: str = "qwen3:4b"):
        self.client = ollama_client or OllamaClient()
        self.model_name = model_name

    def repair_segment(
        self,
        segment: Dict[str, Any],
        issues: List[Dict[str, Any]],
        prev_context: List[str] = None,
        next_context: List[str] = None,
        locked_entities: Optional[Dict[str, str]] = None,
        glossary: Optional[Dict[str, str]] = None,
        translation_style: str = "general",
        custom_translation_style: Optional[str] = None,
        character_metadata: Optional[List[Dict[str, Any]]] = None
    ) -> Dict[str, Any]:
        from autodub.modules.style_profiles import TranslationStyleProfileLoader
        from autodub.modules.character_memory import CharacterEraMemory

        seg_id = segment.get("id")
        orig_text = str(segment.get("text") or segment.get("original_text") or "").strip()
        current_trans = str(segment.get("translated_text") or segment.get("translation") or "").strip()

        issue_messages = [i.get("message", "") for i in issues if i.get("message")]
        issues_summary = "; ".join(issue_messages) if issue_messages else "Potential translation QA failure"

        context_prev_str = "\n".join(prev_context) if prev_context else "N/A"
        context_next_str = "\n".join(next_context) if next_context else "N/A"

        style_data = TranslationStyleProfileLoader.get_profile(translation_style, custom_translation_style)
        style_block = f"TRANSLATION STYLE ({style_data['name'].upper()}):\n{style_data['prompt_instruction']}"
        char_block = CharacterEraMemory.format_character_era_prompt(character_metadata)

        entity_prompt_block = ""
        if locked_entities:
            entity_lines = [f"- {zh} = {vi}" for zh, vi in locked_entities.items()]
            entity_prompt_block = f"LOCKED ENTITY MEMORY (MUST STRICTLY FOLLOW):\n" + "\n".join(entity_lines) + "\n\n"

        glossary_block = ""
        if glossary:
            glossary_lines = [f"- {zh} = {vi}" for zh, vi in glossary.items()]
            glossary_block = f"GLOSSARY TERMINOLOGY:\n" + "\n".join(glossary_lines) + "\n\n"

        prompt = f"""You are a professional Chinese-to-Vietnamese subtitle translation repair engine.
Fix the Vietnamese translation based on original Chinese text, translation style rules, and QA error feedback.

ORIGINAL CHINESE:
"{orig_text}"

CURRENT VIETSUB:
"{current_trans}"

PREVIOUS SUBTITLES:
{context_prev_str}

NEXT SUBTITLES:
{context_next_str}

{style_block}

{char_block}

{entity_prompt_block}{glossary_block}QA ERRORS DETECTED:
- {issues_summary}

RULES:
1. Return ONLY a JSON object: {{"translation": "CORRECTED_VIETNAMESE_SUBTITLE"}}
2. Strictly follow LOCKED ENTITY MEMORY and GLOSSARY if specified.
3. Respect Translation Style and Character Era Metadata.
4. Fix all QA errors, unnatural phrasing, pronoun mismatches, and foreign text leakage.
5. Do NOT add explanation, commentary, note, or extra fields."""

        system_prompt = "You are a precise subtitle translation repair assistant. Return valid JSON only."

        repaired_text = current_trans
        source = "ollama"

        try:
            available, _msg = self.client.check_availability(self.model_name)
            if available:
                raw_reply = self.client.generate(
                    prompt=prompt,
                    system=system_prompt,
                    model=self.model_name,
                    timeout=30
                )
                
                # Parse structured output
                parsed_valid, extracted_text, parse_err = StructuredParser.parse_translation_response(raw_reply)
                if parsed_valid:
                    repaired_text = TranslationOutputSanitizer.sanitize(extracted_text)
                else:
                    logger.warning(f"Repair JSON parse failed for segment #{seg_id}: {parse_err}")
                    repaired_text = TranslationOutputSanitizer.sanitize(raw_reply)
            else:
                source = "offline"
                repaired_text = current_trans
        except Exception as e:
            logger.warning(f"AI Repair attempt failed for segment #{seg_id}: {e}")
            source = "offline"

        # Evaluate candidate segment with QA #2
        candidate_seg = {**segment, "translated_text": repaired_text}
        qa2_result = TranslationQaChecker.check_segment(candidate_seg, locked_entities=locked_entities)

        # Final decision policy: Strict 1-Pass Repair Limit
        if qa2_result["status"] == "PASS":
            decision = "AUTO_ACCEPT"
        else:
            decision = "HUMAN_REVIEW"

        provenance = {
            "source": source,
            "model": self.model_name,
            "repair": True,
            "repair_pass": 1,
            "qa2_status": qa2_result["status"],
            "qa2_score": qa2_result["score"],
            "decision": decision
        }

        return {
            "segment_id": seg_id,
            "original_text": orig_text,
            "previous_translation": current_trans,
            "suggested_translation": repaired_text if decision == "AUTO_ACCEPT" else current_trans,
            "repaired_translation": repaired_text,
            "qa_score_after": qa2_result["score"],
            "decision": decision,
            "provenance": provenance
        }
