from typing import Dict, Any, List, Tuple
from autodub.novel.engines.base_engine import BaseDomainEngine
from autodub.novel.prompts.open_thread_prompt import OpenThreadPrompt


class OpenThreadEngine(BaseDomainEngine):
    def __init__(self, llm_client: Any):
        super().__init__("open_thread", llm_client)

    def analyze_chapter(
        self,
        chapter_num: int,
        chapter_text: str,
        active_threads: List[Dict[str, Any]],
        relevant_canon: List[Dict[str, Any]]
    ) -> Tuple[Dict[str, Any], Dict[str, Any]]:
        """Processes ONLY open narrative threads (NEW, ACTIVE, PROGRESSING, RESOLVED, CANCELLED)."""
        prompt = OpenThreadPrompt.build_prompt(chapter_num, chapter_text, active_threads, relevant_canon)
        delta_payload, metadata = self.extract_delta(prompt, chapter_num)

        updates = delta_payload.get("open_thread_updates", [])
        if not isinstance(updates, list):
            updates = []

        delta_payload["open_thread_updates"] = updates
        return delta_payload, metadata
