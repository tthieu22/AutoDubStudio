from typing import Dict, Any, List, Tuple
from autodub.novel.engines.base_engine import BaseDomainEngine
from autodub.novel.prompts.relationship_prompt import RelationshipPrompt


class RelationshipEngine(BaseDomainEngine):
    def __init__(self, llm_client: Any):
        super().__init__("relationship", llm_client)

    def analyze_chapter(
        self,
        chapter_num: int,
        chapter_text: str,
        existing_relationships: List[Dict[str, Any]],
        relevant_characters: List[Dict[str, Any]]
    ) -> Tuple[Dict[str, Any], Dict[str, Any]]:
        """Processes ONLY character and faction relationship changes."""
        prompt = RelationshipPrompt.build_prompt(chapter_num, chapter_text, existing_relationships, relevant_characters)
        delta_payload, metadata = self.extract_delta(prompt, chapter_num)

        updates = delta_payload.get("relationship_updates", [])
        if not isinstance(updates, list):
            updates = []

        delta_payload["relationship_updates"] = updates
        return delta_payload, metadata
