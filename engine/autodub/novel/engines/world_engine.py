from typing import Dict, Any, List, Tuple
from autodub.novel.engines.base_engine import BaseDomainEngine
from autodub.novel.prompts.world_prompt import WorldPrompt


class WorldEngine(BaseDomainEngine):
    def __init__(self, llm_client: Any):
        super().__init__("world", llm_client)

    def analyze_chapter(
        self,
        chapter_num: int,
        chapter_text: str,
        existing_world: Dict[str, Any],
        relevant_canon: List[Dict[str, Any]]
    ) -> Tuple[Dict[str, Any], Dict[str, Any]]:
        """Processes ONLY world locations, factions, and region status changes."""
        prompt = WorldPrompt.build_prompt(chapter_num, chapter_text, existing_world, relevant_canon)
        delta_payload, metadata = self.extract_delta(prompt, chapter_num)

        w_updates = delta_payload.get("world_updates", {})
        if not isinstance(w_updates, dict):
            w_updates = {}
        delta_payload["world_updates"] = w_updates

        return delta_payload, metadata
