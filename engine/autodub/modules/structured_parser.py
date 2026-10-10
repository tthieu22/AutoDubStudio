import json
import re
import ast
from typing import Tuple, Dict, Any, Optional, Union
from autodub.modules.llamacpp_client import strip_think_tags

class StructuredParser:
    """Structured Output Parser for Ollama/LLM JSON responses.
    Validates JSON format strictly and extracts translation text or structured payloads.
    If parsing fails, returns is_valid=False with reason.
    """

    @staticmethod
    def extract_json_payload(raw_text: str) -> Optional[Union[Dict[str, Any], list]]:
        """
        Robust multi-strategy extraction for JSON objects ({}) or arrays ([]).
        Strips think tags, markdown code blocks, prose wrappers, JS comments,
        smart quotes, and trailing commas.
        """
        if not raw_text or not raw_text.strip():
            return None

        cleaned = strip_think_tags(raw_text).strip()
        cleaned = re.sub(r"```(?:json)?\s*", "", cleaned, flags=re.IGNORECASE)
        cleaned = re.sub(r"```\s*", "", cleaned).strip()

        def sanitize(s: str) -> str:
            s = re.sub(r"//.*?\n", "\n", s)
            s = re.sub(r"/\*[\s\S]*?\*/", "", s)
            s = s.replace("“", '"').replace("”", '"').replace("’", "'")
            s = re.sub(r",\s*([\]}])", r"\1", s)
            return s

        # Strategy 1: Direct JSON parse
        try:
            return json.loads(cleaned, strict=False)
        except Exception:
            pass

        try:
            return json.loads(sanitize(cleaned), strict=False)
        except Exception:
            pass

        # Strategy 2: Cut prose surrounding top-level { ... } or [ ... ]
        first_brace = cleaned.find("{")
        first_bracket = cleaned.find("[")

        if first_brace != -1 and (first_bracket == -1 or first_brace < first_bracket):
            last_brace = cleaned.rfind("}")
            if last_brace > first_brace:
                cand = cleaned[first_brace:last_brace + 1]
                try:
                    return json.loads(cand, strict=False)
                except Exception:
                    try:
                        return json.loads(sanitize(cand), strict=False)
                    except Exception:
                        try:
                            res_eval = ast.literal_eval(sanitize(cand))
                            if isinstance(res_eval, dict):
                                return res_eval
                        except Exception:
                            pass

        if first_bracket != -1 and (first_brace == -1 or first_bracket < first_brace):
            last_bracket = cleaned.rfind("]")
            if last_bracket > first_bracket:
                cand = cleaned[first_bracket:last_bracket + 1]
                try:
                    return json.loads(cand, strict=False)
                except Exception:
                    try:
                        return json.loads(sanitize(cand), strict=False)
                    except Exception:
                        try:
                            res_eval = ast.literal_eval(sanitize(cand))
                            if isinstance(res_eval, list):
                                return res_eval
                        except Exception:
                            pass

        return None

    @staticmethod
    def parse_translation_response(raw_text: str) -> Tuple[bool, str, str]:
        """
        Parses raw text response from LLM into (is_valid, translation_text, error_reason).
        Expects JSON object containing 'translation' or 'translated_text'.
        """
        if not raw_text or not raw_text.strip():
            return False, "", "Empty response received from model"

        payload = StructuredParser.extract_json_payload(raw_text)
        if payload is None:
            return False, "", "Failed to extract valid JSON from response"

        if not isinstance(payload, dict):
            return False, "", "Parsed JSON is not an object"

        translation = payload.get("translation") or payload.get("translated_text") or payload.get("vietnamese")
        if translation is None:
            return False, "", "JSON missing required 'translation' key"

        translation_str = str(translation).strip()
        if not translation_str:
            return False, "", "Translation string in JSON is empty"

        return True, translation_str, ""

