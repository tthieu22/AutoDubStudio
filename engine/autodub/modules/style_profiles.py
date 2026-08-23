import os
import json
from pathlib import Path
from typing import Dict, Any, Optional

PROFILES_DIR = Path(__file__).resolve().parent.parent / "translation_profiles"

class TranslationStyleProfileLoader:
    """Data-driven Style Profile Loader.
    Loads profile instructions from JSON files in translation_profiles/ without any hardcoded dictionary replacements.
    """
    _cache: Dict[str, Dict[str, Any]] = {}

    @classmethod
    def get_profile(cls, style_id: str, custom_instruction: Optional[str] = None) -> Dict[str, Any]:
        style_id = (style_id or "general").lower().strip()
        
        if style_id == "custom":
            custom_text = (custom_instruction or "").strip()
            prompt = f"TRANSLATION STYLE: CUSTOM USER INSTRUCTIONS\n{custom_text}" if custom_text else "TRANSLATION STYLE: GENERAL / AUTOMATIC CONVERSATIONAL\n- Translate into natural, fluent Vietnamese spoken dialogue."
            return {
                "id": "custom",
                "name": "Tùy chỉnh",
                "description": "User-defined custom translation style instructions",
                "prompt_instruction": prompt,
                "custom_instruction": custom_text
            }

        if style_id in cls._cache:
            return cls._cache[style_id]

        file_path = PROFILES_DIR / f"{style_id}.json"
        if not file_path.exists():
            # Fallback to general.json if specified profile file is missing
            file_path = PROFILES_DIR / "general.json"

        try:
            with open(file_path, "r", encoding="utf-8") as f:
                data = json.load(f)
                cls._cache[style_id] = data
                return data
        except Exception as e:
            return {
                "id": style_id,
                "name": style_id.capitalize(),
                "description": f"Fallback profile for {style_id}",
                "prompt_instruction": "TRANSLATION STYLE: GENERAL / AUTOMATIC CONVERSATIONAL\n- Translate into natural, fluent spoken Vietnamese."
            }

    @classmethod
    def list_available_profiles(cls) -> list:
        profiles = []
        if PROFILES_DIR.exists():
            for f in sorted(PROFILES_DIR.glob("*.json")):
                try:
                    with open(f, "r", encoding="utf-8") as file:
                        data = json.load(file)
                        profiles.append(data)
                except Exception:
                    pass
        return profiles
