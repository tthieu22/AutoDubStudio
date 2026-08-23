from typing import List, Dict, Any, Optional

class CharacterEraMemory:
    """Character Era & Relationship Memory for Time Travel and Era-Sensitive Subtitle Translation."""

    @staticmethod
    def format_character_era_prompt(character_metadata: Optional[List[Dict[str, Any]]] = None) -> str:
        if not character_metadata:
            return ""

        lines = ["CHARACTER & ERA MEMORY (MUST MAINTAIN ERA & RELATIONAL DYNAMICS):"]
        for meta in character_metadata:
            char_name = meta.get("character", "Unknown")
            era = meta.get("era", "modern")
            rel = meta.get("relationship", "")
            pronouns = meta.get("preferred_pronouns", "")

            era_str = "MODERN ERA CHARACTER (Use contemporary spoken Vietnamese)" if era == "modern" else "ANCIENT ERA CHARACTER (Use historical period-drama spoken Vietnamese)"
            details = []
            if rel:
                details.append(f"Role/Relation: {rel}")
            if pronouns:
                details.append(f"Preferred Pronouns: {pronouns}")
            
            detail_str = f" ({', '.join(details)})" if details else ""
            lines.append(f"- {char_name}: {era_str}{detail_str}")

        return "\n".join(lines) + "\n\n"
