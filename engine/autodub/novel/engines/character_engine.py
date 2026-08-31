from typing import Dict, Any, List, Tuple
from autodub.novel.engines.base_engine import BaseDomainEngine
from autodub.novel.prompts.character_prompt import CharacterPrompt


class CharacterEngine(BaseDomainEngine):
    def __init__(self, llm_client: Any):
        super().__init__("character", llm_client)

    def analyze_chapter(
        self,
        chapter_num: int,
        chapter_text: str,
        relevant_characters: List[Dict[str, Any]],
        relevant_canon: List[Dict[str, Any]]
    ) -> Tuple[Dict[str, Any], Dict[str, Any]]:
        """Processes ONLY character domain attributes and status updates."""
        prompt = CharacterPrompt.build_prompt(chapter_num, chapter_text, relevant_characters, relevant_canon)
        delta_payload, metadata = self.extract_delta(prompt, chapter_num)

        # Enforce delta schema array format
        updates = delta_payload.get("character_updates", [])
        if not isinstance(updates, list):
            updates = []
        delta_payload["character_updates"] = updates

        return delta_payload, metadata
