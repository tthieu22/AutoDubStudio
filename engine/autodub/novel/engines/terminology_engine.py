from typing import Dict, Any, List, Tuple
from autodub.novel.engines.base_engine import BaseDomainEngine
from autodub.novel.prompts.terminology_prompt import TerminologyPrompt


class TerminologyEngine(BaseDomainEngine):
    def __init__(self, llm_client: Any):
        super().__init__("terminology", llm_client)

    def analyze_chapter(
        self,
        chapter_num: int,
        chapter_text: str,
        existing_terms: Dict[str, str],
        relevant_canon: List[Dict[str, Any]]
    ) -> Tuple[Dict[str, Any], Dict[str, Any]]:
        """Processes ONLY terminology consistency and newly introduced proper nouns."""
        prompt = TerminologyPrompt.build_prompt(chapter_num, chapter_text, existing_terms, relevant_canon)
        delta_payload, metadata = self.extract_delta(prompt, chapter_num)

        updates = delta_payload.get("terminology_updates", [])
        if not isinstance(updates, list):
            updates = []

        delta_payload["terminology_updates"] = updates
        return delta_payload, metadata
