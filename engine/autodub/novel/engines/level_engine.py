from typing import Dict, Any, List, Tuple
from autodub.novel.engines.base_engine import BaseDomainEngine
from autodub.novel.prompts.level_prompt import LevelPrompt


class LevelEngine(BaseDomainEngine):
    def __init__(self, llm_client: Any):
        super().__init__("level", llm_client)

    def analyze_chapter(
        self,
        chapter_num: int,
        chapter_text: str,
        progression_ranks: List[Dict[str, Any]],
        character_current_levels: List[Dict[str, Any]]
    ) -> Tuple[Dict[str, Any], Dict[str, Any]]:
        """Processes ONLY power level & realm breakthrough deltas."""
        prompt = LevelPrompt.build_prompt(chapter_num, chapter_text, progression_ranks, character_current_levels)
        delta_payload, metadata = self.extract_delta(prompt, chapter_num)

        updates = delta_payload.get("level_updates", [])
        if not isinstance(updates, list):
            updates = []

        delta_payload["level_updates"] = updates
        return delta_payload, metadata
