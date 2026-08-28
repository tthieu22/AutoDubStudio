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

    @staticmethod
    def get_character_at_chapter(db, character_id: str, chapter_num: int) -> Optional[Dict[str, Any]]:
        if db:
            return db.get_character_state_at_chapter(character_id, chapter_num)
        return None

    @staticmethod
    def get_known_information(db, character_id: str, chapter_num: int) -> List[str]:
        state = CharacterEraMemory.get_character_at_chapter(db, character_id, chapter_num)
        if state:
            return state.get("known_information", [])
        return []

    @staticmethod
    def update_state_after_chapter(db, state_obj):
        if db:
            db.update_character_state(state_obj)
