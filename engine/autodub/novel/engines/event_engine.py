from typing import Dict, Any, List, Tuple
from autodub.novel.engines.base_engine import BaseDomainEngine
from autodub.novel.prompts.event_prompt import EventPrompt


class EventEngine(BaseDomainEngine):
    def __init__(self, llm_client: Any):
        super().__init__("event", llm_client)

    def analyze_chapter(
        self,
        chapter_num: int,
        chapter_text: str,
        recent_events: List[Dict[str, Any]],
        relevant_canon: List[Dict[str, Any]]
    ) -> Tuple[Dict[str, Any], Dict[str, Any]]:
        """Processes ONLY event chronology, participants, and status (FACT, CLAIM, RUMOR, UNKNOWN)."""
        prompt = EventPrompt.build_prompt(chapter_num, chapter_text, recent_events, relevant_canon)
        delta_payload, metadata = self.extract_delta(prompt, chapter_num)

        updates = delta_payload.get("event_updates", [])
        if not isinstance(updates, list):
            updates = []

        delta_payload["event_updates"] = updates
        return delta_payload, metadata
