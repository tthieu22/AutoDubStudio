import json
import os
import re
import time
import urllib.request
import urllib.error
import socket
import logging
from typing import Tuple, Optional, List, Dict, Any
from autodub.config import TRANSLATION_MODEL, DEFAULT_TRANSLATION_MODEL
from autodub.modules.ollama_model_manager import OllamaModelManager
from autodub.exceptions import (
    TranslationFailedError,
    OllamaUnavailableError,
    OllamaTimeoutError
)

logger = logging.getLogger("autodub")
socket_timeout_types = (socket.timeout, TimeoutError)


def strip_think_tags(text: str) -> str:
    """Strips <think>...</think> reasoning blocks, preamble reasoning, and leading/trailing whitespace."""
    if not text:
        return ""

    # 1. Remove closed and unclosed <think> blocks
    cleaned = re.sub(r'<think>[\s\S]*?</think>', '', text, flags=re.IGNORECASE).strip()
    cleaned = re.sub(r'^<think>[\s\S]*', '', cleaned, flags=re.IGNORECASE).strip()

    # 2. If batch formatted output with [SUBTITLE_XXX], extract from the first subtitle block
    match = re.search(r'(?:\[)?SUBTITLE_\d+(?:\]|\:)?', cleaned, flags=re.IGNORECASE)
    if match:
        cleaned = cleaned[match.start():].strip()
        return cleaned

    # 3. If single sentence output, strip preamble reasoning lines
    lines = [l.strip() for l in cleaned.splitlines() if l.strip()]
    final_lines = []
    for l in lines:
        if re.match(r'^(okay|let me|first|here is|the chinese sentence|this sentence|in vietnamese|analyzing|understanding|translation)\b', l, re.IGNORECASE):
            continue
        final_lines.append(l)

    if final_lines:
        return "\n".join(final_lines).strip()

    return cleaned


class OllamaClient:
    """HTTP client for communicating with local Ollama REST API server with Qwen3 Thinking Mode ON."""
    def __init__(self, base_url: Optional[str] = None):
        if not base_url:
            base_url = os.environ.get("OLLAMA_BASE_URL", "http://localhost:11434")
        self.base_url = base_url.rstrip("/")
        self.model_manager = OllamaModelManager(base_url=self.base_url)
        self.last_metrics: Dict[str, Any] = {}

    def ensure_model_loaded(self, timeout: int = 60) -> Tuple[bool, str]:
        """Delegate to OllamaModelManager to guarantee qwen3:4b is exclusively active in VRAM."""
        return self.model_manager.ensure_qwen3_loaded(timeout=timeout)

    def check_availability(self, model_name: str = TRANSLATION_MODEL) -> Tuple[bool, str]:
        """Check if Ollama is reachable and the specified model is installed."""
        url = f"{self.base_url}/api/tags"
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "AutoDubStudio"})
            with urllib.request.urlopen(req, timeout=5) as response:
                if response.status != 200:
                    return False, f"Ollama returned HTTP status {response.status}"
                data = json.loads(response.read().decode("utf-8"))
        except Exception as e:
            return False, f"Ollama is not running at {self.base_url}"

        models = data.get("models", [])
        installed_names = []
        for m in models:
            name = m.get("name", "")
            model_tag = m.get("model", "")
            installed_names.extend([name, model_tag])

        target_base = model_name.split(":")[0]
        found = False
        for installed in installed_names:
            if not installed:
                continue
            if installed == model_name or installed.startswith(f"{model_name}:"):
                found = True
                break
            if installed == target_base or installed.startswith(f"{target_base}:"):
                found = True
                break

        if not found:
            return False, f"Ollama model '{model_name}' is not installed."

        return True, ""

    def chat(
        self,
        messages: List[Dict[str, str]],
        system: Optional[str] = None,
        model: str = DEFAULT_TRANSLATION_MODEL,
        temperature: float = 0.15,
        num_predict: int = 2048,
        timeout: int = 120
    ) -> str:
        """Call Ollama /api/chat REST endpoint synchronously with Thinking Mode ON (think=True)."""
        url = f"{self.base_url}/api/chat"
        formatted_messages = list(messages)
        if system:
            if not formatted_messages or formatted_messages[0].get("role") != "system":
                formatted_messages.insert(0, {"role": "system", "content": system})

        payload = {
            "model": model,
            "messages": formatted_messages,
            "stream": False,
            "keep_alive": "1h",
            "options": {
                "temperature": temperature,
                "num_predict": num_predict
            }
        }
        if "qwen3" in model.lower() or "think" in model.lower():
            payload["think"] = True

        # MAX_RETRIES = 1 (Total 2 attempts max)
        for attempt in range(1, 3):
            try:
                req = urllib.request.Request(
                    url,
                    data=json.dumps(payload).encode("utf-8"),
                    headers={"Content-Type": "application/json", "User-Agent": "AutoDubStudio"}
                )
                with urllib.request.urlopen(req, timeout=timeout) as resp:
                    result = json.loads(resp.read().decode("utf-8"))
                    self._record_metrics(result)
                    msg = result.get("message", {})
                    response_text = strip_think_tags(msg.get("content", ""))
                    if response_text:
                        return response_text
                    logger.warning(f"[OLLAMA] Chat response attempt #{attempt} for '{model}' was empty.")
            except (urllib.error.URLError, socket.timeout, TimeoutError, Exception) as e:
                logger.warning(f"[OLLAMA] Chat attempt #{attempt} error: {e}")
                if attempt == 2:
                    if "timed out" in str(e).lower() or isinstance(e, (socket.timeout, TimeoutError)):
                        raise OllamaTimeoutError(f"Ollama chat request for model '{model}' timed out after {timeout} seconds.")
                    raise TranslationFailedError(f"Ollama API chat request for model '{model}' failed: {e}")
                time.sleep(1)

        raise TranslationFailedError(f"Ollama chat request for model '{model}' returned empty content after 1 retry.")

    def generate(
        self,
        prompt: str,
        system: Optional[str] = None,
        model: str = DEFAULT_TRANSLATION_MODEL,
        temperature: float = 0.15,
        format_json: bool = False,
        timeout: int = 120,
        num_predict: int = 1024
    ) -> str:
        """Call Ollama /api/generate REST endpoint synchronously with model-aware parameters."""
        url = f"{self.base_url}/api/generate"

        current_predict = num_predict

        # MAX_RETRIES = 1 (Total 2 attempts max)
        for attempt in range(1, 3):
            payload = {
                "model": model,
                "prompt": prompt,
                "stream": False,
                "keep_alive": "1h",
                "options": {
                    "temperature": temperature,
                    "num_predict": current_predict
                }
            }
            if "qwen3" in model.lower() or "think" in model.lower():
                payload["think"] = True
            if format_json and not model.startswith("qwen3"):
                payload["format"] = "json"
            if system:
                payload["system"] = system

            try:
                req = urllib.request.Request(
                    url,
                    data=json.dumps(payload).encode("utf-8"),
                    headers={"Content-Type": "application/json", "User-Agent": "AutoDubStudio"}
                )
                with urllib.request.urlopen(req, timeout=timeout) as resp:
                    result = json.loads(resp.read().decode("utf-8"))
                    self._record_metrics(result)
                    raw = result.get("response", "")
                    done_reason = result.get("done_reason", "")
                    thinking = result.get("thinking", "")
                    response_text = strip_think_tags(raw)
                    
                    if response_text:
                        self.last_status = "SUCCESS"
                        return response_text
                    
                    if done_reason == "length":
                        logger.warning(f"[OLLAMA] Token budget exhausted for '{model}' (num_predict={current_predict}, eval_count={result.get('eval_count')}).")
                        self.last_status = "TOKEN_BUDGET_EXHAUSTED"
                        # Increase budget on the single retry
                        current_predict = min(2048, current_predict + 512)
                    elif thinking and not raw:
                        self.last_status = "THINKING_ONLY"
                        logger.warning(f"[OLLAMA] Thinking only returned for '{model}'.")
                        current_predict = min(2048, current_predict + 512)
                    else:
                        self.last_status = "EMPTY_RESPONSE"
                        logger.warning(f"[OLLAMA] Generate response attempt #{attempt} for '{model}' was empty.")
            except (urllib.error.URLError, socket.timeout, TimeoutError, Exception) as e:
                logger.warning(f"[OLLAMA] Generate attempt #{attempt} error: {e}")
                if attempt == 2:
                    if "timed out" in str(e).lower() or isinstance(e, (socket.timeout, TimeoutError)):
                        raise OllamaTimeoutError(f"Ollama generate request timed out after {timeout} seconds.")
                    raise TranslationFailedError(f"Ollama API request failed: {e}")
                time.sleep(1)

        raise TranslationFailedError(f"Ollama generate request for model '{model}' failed after 1 retry (Status: {getattr(self, 'last_status', 'EMPTY_RESPONSE')}).")

    def _record_metrics(self, res_json: Dict[str, Any]):
        """Extract and log Ollama performance metrics."""
        total_duration_sec = res_json.get("total_duration", 0) / 1e9
        load_duration_sec = res_json.get("load_duration", 0) / 1e9
        prompt_eval_sec = res_json.get("prompt_eval_duration", 0) / 1e9
        prompt_eval_count = res_json.get("prompt_eval_count", 0)
        eval_sec = res_json.get("eval_duration", 0) / 1e9
        eval_count = res_json.get("eval_count", 0)
        tokens_per_sec = (eval_count / eval_sec) if eval_sec > 0 else 0.0
        done_reason = res_json.get("done_reason", "stop")
        thinking = res_json.get("thinking", "")
        response = res_json.get("response", "")

        thinking_tokens = eval_count if (thinking and not response) else 0
        response_tokens = eval_count - thinking_tokens if thinking_tokens > 0 else eval_count

        self.last_metrics = {
            "total_duration_sec": total_duration_sec,
            "load_duration_sec": load_duration_sec,
            "prompt_eval_sec": prompt_eval_sec,
            "prompt_eval_count": prompt_eval_count,
            "eval_sec": eval_sec,
            "eval_count": eval_count,
            "tokens_per_sec": tokens_per_sec,
            "done_reason": done_reason,
            "thinking_tokens": thinking_tokens,
            "response_tokens": response_tokens
        }
        logger.debug(f"[OLLAMA_METRICS] Total: {total_duration_sec:.2f}s | Speed: {tokens_per_sec:.1f} tok/s | Tokens: {eval_count} | DoneReason: {done_reason}")
        logger.info(
            f"[OLLAMA] Model={res_json.get('model', 'qwen3:4b')} | Thinking=ON | "
            f"Total={total_duration_sec:.2f}s | Load={load_duration_sec:.2f}s | "
            f"PromptEval={prompt_eval_sec:.2f}s ({prompt_eval_count} toks) | "
            f"Gen={eval_sec:.2f}s ({eval_count} toks) | "
            f"Speed={tokens_per_sec:.2f} toks/s"
        )

