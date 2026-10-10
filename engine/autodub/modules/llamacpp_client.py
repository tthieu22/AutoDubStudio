import json
import os
import re
import time
import urllib.request
import urllib.error
import socket
import logging
from pathlib import Path
from typing import Tuple, Optional, List, Dict, Any
from autodub.config import TRANSLATION_MODEL
from autodub.modules.llamacpp_model_manager import LlamaCppModelManager
from autodub.exceptions import (
    TranslationFailedError,
    LlamaCppUnavailableError,
    LlamaCppTimeoutError
)

logger = logging.getLogger("autodub")
socket_timeout_types = (socket.timeout, TimeoutError)


def strip_think_tags(text: str) -> str:
    """Strips <think>...</think> reasoning blocks, preamble reasoning, and leading/trailing whitespace."""
    if not text:
        return ""

    cleaned = text.strip()

    # 1. Strip closed <think>...</think> blocks first
    cleaned = re.sub(r'<think>[\s\S]*?</think>', '', cleaned, flags=re.IGNORECASE).strip()

    # 2. Handle unclosed <think> blocks (where </think> is missing)
    if '<think>' in cleaned.lower():
        # Check if JSON array/object or subtitle marker starts inside/after <think>
        json_match = re.search(r'([\[\{])', cleaned)
        sub_match = re.search(r'(?:\[)?SUBTITLE_\d+(?:\]|\:)?', cleaned, flags=re.IGNORECASE)

        if json_match:
            # Keep payload from the first JSON bracket onward
            cleaned = cleaned[json_match.start():].strip()
        elif sub_match:
            cleaned = cleaned[sub_match.start():].strip()
        else:
            # If no bracket found, strip think tag line or tag itself safely
            cleaned = re.sub(r'<think>.*?\n', '', cleaned, flags=re.IGNORECASE).strip()
            cleaned = re.sub(r'<think>', '', cleaned, flags=re.IGNORECASE).strip()

    # 3. If batch formatted output with [SUBTITLE_XXX], extract from the first subtitle block
    match = re.search(r'(?:\[)?SUBTITLE_\d+(?:\]|\:)?', cleaned, flags=re.IGNORECASE)
    if match:
        cleaned = cleaned[match.start():].strip()
        return cleaned

    # 4. Strip preamble reasoning lines ONLY if response does NOT contain JSON structures
    first_bracket = cleaned.find('[')
    first_brace = cleaned.find('{')
    has_json = (first_bracket != -1 or first_brace != -1)

    if not has_json:
        lines = [l.strip() for l in cleaned.splitlines() if l.strip()]
        final_lines = []
        for l in lines:
            if re.match(r'^(okay|let me|first|here is|the chinese sentence|this sentence|in vietnamese|analyzing|understanding|translation)\b', l, re.IGNORECASE):
                continue
            final_lines.append(l)
        if final_lines:
            return "\n".join(final_lines).strip()

    return cleaned


class LlamaCppClient:
    """HTTP client for communicating with local llama.cpp REST API server (OpenAI / native completion format) for Qwen2.5-3B-Instruct."""

    def __init__(self, base_url: Optional[str] = None):
        if not base_url:
            base_url = os.environ.get("LLAMACPP_BASE_URL", os.environ.get("LLAMA_SERVER_URL", os.environ.get("LOCAL_LLM_URL", "")))
        
        if not base_url:
            base_url = self._detect_active_url()

        self.base_url = base_url.rstrip("/")
        self.model_manager = LlamaCppModelManager(base_url=self.base_url)
        self.last_metrics: Dict[str, Any] = {}

    def _detect_active_url(self) -> str:
        """Detects active local LLM server URL (port 11434 Ollama or 8080 llama.cpp)."""
        candidate_urls = [
            "http://localhost:11434",
            "http://localhost:8080",
            "http://localhost:1234",
            "http://localhost:8000"
        ]
        for test_url in candidate_urls:
            try:
                check_endpoint = f"{test_url}/v1/models"
                req = urllib.request.Request(check_endpoint, method="GET")
                with urllib.request.urlopen(req, timeout=0.6) as resp:
                    if resp.status in (200, 204):
                        return test_url
            except Exception:
                pass

        auto_url = self._auto_start_ollama_if_needed()
        return auto_url or "http://localhost:11434"

    def _auto_start_ollama_if_needed(self) -> Optional[str]:
        """Auto-spawns Ollama background daemon on port 11434 if no local LLM server is active."""
        import shutil
        import subprocess
        import time
        import urllib.request

        ollama_bin = shutil.which("ollama") or r"C:\Users\hieut\AppData\Local\Programs\Ollama\ollama.exe"
        if Path(ollama_bin).exists():
            try:
                logger.info(f"[INFO] [AUTO-LAUNCH] Đang tự động kích hoạt Ollama GPU Server ({ollama_bin})...")
                subprocess.Popen(
                    [str(ollama_bin), "serve"],
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                    creationflags=subprocess.CREATE_NO_WINDOW if os.name == "nt" else 0
                )
                time.sleep(2.0)
                # Verify port 11434 status
                for _ in range(10):
                    try:
                        req = urllib.request.Request("http://localhost:11434/v1/models", method="GET")
                        with urllib.request.urlopen(req, timeout=1) as resp:
                            if resp.status in (200, 204):
                                logger.info("[SUCCESS] [AUTO-LAUNCH] Ollama GPU Server (http://localhost:11434) ready!")
                                return "http://localhost:11434"
                    except Exception:
                        time.sleep(0.5)
            except Exception as e:
                logger.warning(f"Auto-start Ollama failed: {e}")
        return None

    def ensure_model_loaded(self, timeout: int = 60) -> Tuple[bool, str]:
        """Delegate to LlamaCppModelManager to guarantee llama-server is healthy."""
        return self.model_manager.ensure_qwen25_loaded(timeout=timeout)

    def check_availability(self, model_name: str = TRANSLATION_MODEL) -> Tuple[bool, str]:
        """Check if local LLM server is reachable."""
        if "11434" in self.base_url:
            return True, "Ollama GPU server at http://localhost:11434 is active."
        healthy, msg = self.model_manager.check_health()
        if not healthy:
            return False, f"Local LLM server is not running at {self.base_url}: {msg}"
        return True, ""

    def chat(
        self,
        messages: List[Dict[str, str]],
        model_name: str = TRANSLATION_MODEL,
        options: Optional[Dict[str, Any]] = None,
        timeout: int = 120,
        system: Optional[str] = None,
        model: Optional[str] = None,
        **kwargs
    ) -> str:
        """
        Sends a multi-turn chat completion request to local LLM REST API.
        Uses OpenAI compatible /v1/chat/completions endpoint.
        """
        if model and not model_name:
            model_name = model

        # Auto-map model_name for Ollama if running on 11434
        if "11434" in self.base_url or model_name.endswith(".gguf"):
            if "11434" in self.base_url:
                model_name = "qwen2.5:3b"

        if system:
            messages = [{"role": "system", "content": system}] + list(messages)

        if not options:
            options = {}
        if kwargs:
            options.update(kwargs)

        temperature = options.get("temperature", 0.1)
        top_p = options.get("top_p", 0.9)
        max_tokens = options.get("max_tokens", options.get("num_predict", 1024))

        # Try /v1/chat/completions with auto-retry & keep_alive
        payload: Dict[str, Any] = {
            "model": model_name,
            "messages": messages,
            "temperature": temperature,
            "top_p": top_p,
            "max_tokens": max_tokens,
            "stream": False,
            "keep_alive": "24h"
        }
        if options.get("json_format", True):
            payload["response_format"] = {"type": "json_object"}

        data_bytes = json.dumps(payload).encode("utf-8")
        res_data = None
        t0 = time.time()

        for attempt in range(2):
            url = f"{self.base_url}/v1/chat/completions"
            req = urllib.request.Request(
                url,
                data=data_bytes,
                headers={"Content-Type": "application/json", "User-Agent": "AutoDubStudio"}
            )
            try:
                with urllib.request.urlopen(req, timeout=timeout) as response:
                    if response.status != 200:
                        raise TranslationFailedError(f"llama.cpp returned HTTP status {response.status}")
                    res_data = json.loads(response.read().decode("utf-8"))
                    break
            except Exception as e:
                logger.warning(f"LLM chat attempt {attempt + 1} failed ({self.base_url}): {e}. Re-detecting active LLM server...")
                reconnected_url = self._detect_active_url()
                if reconnected_url:
                    self.base_url = reconnected_url.rstrip("/")
                else:
                    if attempt == 1:
                        return self._fallback_native_completion(messages, options, timeout)

        if not res_data:
            return self._fallback_native_completion(messages, options, timeout)

        # Extract text response from OpenAI format
        choices = res_data.get("choices", [])
        if not choices:
            raise TranslationFailedError("Empty choices array in llama.cpp response")

        content = choices[0].get("message", {}).get("content", "")
        duration = time.time() - t0
        self.last_metrics = {
            "eval_duration_sec": duration,
            "prompt_tokens": res_data.get("usage", {}).get("prompt_tokens", 0),
            "eval_tokens": res_data.get("usage", {}).get("completion_tokens", 0),
        }

        return strip_think_tags(content)

    def generate(
        self,
        prompt: str,
        system: Optional[str] = None,
        model_name: str = TRANSLATION_MODEL,
        options: Optional[Dict[str, Any]] = None,
        timeout: int = 120
    ) -> str:
        """Sends a text completion / generation prompt to llama.cpp."""
        sys_prompt = system or "Bạn là AI Story Director chuyên sáng tạo tiểu thuyết. Bạn BẮT BUỘC chỉ trả về duy nhất 1 chuỗi RAW JSON hợp lệ (JSON Object hoặc JSON Array). CẤM kèm bất kỳ lời dẫn hay văn bản giải thích nào ngoài JSON."
        messages = [
            {"role": "system", "content": sys_prompt},
            {"role": "user", "content": prompt}
        ]

        return self.chat(messages=messages, model_name=model_name, options=options, timeout=timeout)

    def _fallback_native_completion(
        self,
        messages: List[Dict[str, str]],
        options: Dict[str, Any],
        timeout: int
    ) -> str:
        """Fallback to native llama.cpp /completion or /completions endpoint using ChatML format for Qwen2.5."""
        prompt_parts = []
        for msg in messages:
            role = msg.get("role", "user")
            content = msg.get("content", "")
            prompt_parts.append(f"<|im_start|>{role}\n{content}<|im_end|>")
        prompt_parts.append("<|im_start|>assistant\n")
        full_prompt = "\n".join(prompt_parts)

        url = f"{self.base_url}/completion"
        payload = {
            "prompt": full_prompt,
            "temperature": options.get("temperature", 0.1),
            "top_p": options.get("top_p", 0.9),
            "n_predict": options.get("max_tokens", options.get("num_predict", 1024)),
            "stop": ["<|im_end|>", "<|endoftext|>"]
        }

        req = urllib.request.Request(
            url,
            data=json.dumps(payload).encode("utf-8"),
            headers={"Content-Type": "application/json", "User-Agent": "AutoDubStudio"}
        )

        t0 = time.time()
        try:
            with urllib.request.urlopen(req, timeout=timeout) as response:
                if response.status != 200:
                    raise TranslationFailedError(f"llama.cpp native completion returned HTTP status {response.status}")
                res_data = json.loads(response.read().decode("utf-8"))
        except urllib.error.URLError as e:
            if isinstance(e.reason, socket_timeout_types):
                raise LlamaCppTimeoutError(f"llama.cpp request timed out after {timeout} seconds.")
            raise LlamaCppUnavailableError(f"llama.cpp is unreachable at {self.base_url}")
        except socket_timeout_types:
            raise LlamaCppTimeoutError(f"llama.cpp request timed out after {timeout} seconds.")
        except Exception as e:
            raise LlamaCppUnavailableError(f"Failed to communicate with llama.cpp native endpoint: {e}")

        content = res_data.get("content", res_data.get("text", ""))
        self.last_metrics = {
            "eval_duration_sec": time.time() - t0,
            "tokens_predicted": res_data.get("tokens_predicted", 0)
        }
        return strip_think_tags(content)


# Alias for backward compatibility with OllamaClient imports
OllamaClient = LlamaCppClient
