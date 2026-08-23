import json
import re
from typing import Tuple, Dict, Any, Optional

class StructuredParser:
    """Structured Output Parser for Ollama JSON responses.
    Validates JSON format strictly and extracts translation text.
    If parsing fails, returns is_valid=False with reason.
    """

    @staticmethod
    def parse_translation_response(raw_text: str) -> Tuple[bool, str, str]:
        """
        Parses raw text response from LLM into (is_valid, translation_text, error_reason).
        Expects JSON object containing 'translation' or 'translated_text'.
        """
        if not raw_text or not raw_text.strip():
            return False, "", "Empty response received from model"

        text = raw_text.strip()

        # Handle markdown code blocks
        if "```" in text:
            match = re.search(r'```(?:json)?\s*(\{[\s\S]*?\})\s*```', text)
            if match:
                text = match.group(1).strip()

        # Extract first JSON object if surrounded by prose
        if not (text.startswith("{") and text.endswith("}")):
            match = re.search(r'(\{[\s\S]*\})', text)
            if match:
                text = match.group(1).strip()

        try:
            data = json.loads(text)
            if not isinstance(data, dict):
                return False, "", "Parsed JSON is not an object"

            translation = data.get("translation") or data.get("translated_text") or data.get("vietnamese")
            if translation is None:
                return False, "", "JSON missing required 'translation' key"

            translation_str = str(translation).strip()
            if not translation_str:
                return False, "", "Translation string in JSON is empty"

            return True, translation_str, ""

        except json.JSONDecodeError as e:
            return False, "", f"JSON decode error: {e}"
