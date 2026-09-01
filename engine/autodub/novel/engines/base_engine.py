import time
import logging
from typing import Dict, Any, Optional, Tuple
from autodub.novel.novel_models import GenerationError, GenerationErrorCode

logger = logging.getLogger(__name__)


class BaseDomainEngine:
    """Abstract Base Class for Specialized Prompt Engines."""

    def __init__(self, domain_name: str, llm_client: Any):
        self.domain_name = domain_name
        self.llm_client = llm_client

    def log_execution(self, chapter_num: int, input_size: int, output_size: int, execution_time: float, status: str, failure_reason: Optional[str] = None):
        """Structured per-engine logging."""
        log_msg = (
            f"[{self.domain_name.upper()}_ENGINE] Chapter: {chapter_num} | Status: {status} | "
            f"Execution: {execution_time:.2f}s | InBytes: {input_size} | OutBytes: {output_size}"
        )
        if failure_reason:
            log_msg += f" | FailureReason: {failure_reason}"

        if status == "PASS":
            logger.info(log_msg)
        else:
            logger.warning(log_msg)

    def extract_delta(self, prompt: str, chapter_num: int, max_retries: int = 2) -> Tuple[Dict[str, Any], Dict[str, Any]]:
        """Executes LLM call with domain-isolated logging and error handling."""
        start_time = time.time()
        input_size = len(prompt.encode("utf-8"))

        for attempt in range(1, max_retries + 1):
            try:
                raw_text = self.llm_client.generate(prompt=prompt)
                output_size = len(raw_text.encode("utf-8")) if raw_text else 0

                if not raw_text or not raw_text.strip():
                    self.log_execution(chapter_num, input_size, 0, time.time() - start_time, "FAIL", "LLM returned empty response")
                    continue

                from autodub.modules.llamacpp_client import strip_think_tags
                cleaned_raw = strip_think_tags(raw_text).strip() if raw_text else ""

                if hasattr(self.llm_client, "extract_json"):
                    parsed_json = self.llm_client.extract_json(cleaned_raw)
                else:
                    from autodub.modules.structured_parser import StructuredParser
                    parsed_json = StructuredParser.extract_json_payload(cleaned_raw)

                if parsed_json is None or not isinstance(parsed_json, (dict, list)):
                    self.log_execution(chapter_num, input_size, output_size, time.time() - start_time, "FAIL", "JSON Parse Error")
                    continue


                exec_time = time.time() - start_time
                self.log_execution(chapter_num, input_size, output_size, exec_time, "PASS")
                metadata = {
                    "domain": self.domain_name,
                    "execution_time": exec_time,
                    "attempt": attempt,
                    "status": "PASS"
                }
                return parsed_json if isinstance(parsed_json, dict) else {f"{self.domain_name}_updates": parsed_json}, metadata

            except Exception as e:
                exec_time = time.time() - start_time
                self.log_execution(chapter_num, input_size, 0, exec_time, "FAIL", str(e))
                if attempt == max_retries:
                    raise GenerationError(
                        self.domain_name.upper(),
                        GenerationErrorCode.LLM_GENERATION_FAILED.value,
                        f"[{self.domain_name.upper()}_ENGINE] Failed after {max_retries} attempts: {e}"
                    )

        # Fail-closed
        raise GenerationError(
            self.domain_name.upper(),
            GenerationErrorCode.SCHEMA_VALIDATION_ERROR.value,
            f"[{self.domain_name.upper()}_ENGINE] Failed to extract valid delta payload"
        )
