from typing import Dict, Any, List, Tuple
from autodub.novel.engines.base_engine import BaseDomainEngine
from autodub.novel.prompts.memory_prompt import MemoryPrompt


class MemoryEngine(BaseDomainEngine):
    def __init__(self, llm_client: Any):
        super().__init__("memory", llm_client)

    def analyze_chapter(
        self,
        chapter_num: int,
        chapter_text: str,
        relevant_characters: List[Dict[str, Any]],
        known_memory: List[Dict[str, Any]]
    ) -> Tuple[Dict[str, Any], Dict[str, Any]]:
        """Processes ONLY character knowledge state updates (UNKNOWN, RUMOR, CLAIM, CONFIRMED)."""
        prompt = MemoryPrompt.build_prompt(chapter_num, chapter_text, relevant_characters, known_memory)
        delta_payload, metadata = self.extract_delta(prompt, chapter_num)

        updates = delta_payload.get("memory_updates", [])
        if not isinstance(updates, list):
            updates = []

        # Validate information states
        valid_states = {"UNKNOWN", "RUMOR", "CLAIM", "CONFIRMED"}
        sanitized_updates = []
        for u in updates:
            if isinstance(u, dict):
                state = u.get("information_state", "CONFIRMED").upper()
                if state not in valid_states:
                    state = "CONFIRMED"
                u["information_state"] = state
                sanitized_updates.append(u)

        delta_payload["memory_updates"] = sanitized_updates
        return delta_payload, metadata
