import json
import os
import re
import time
import urllib.request
import urllib.error
import socket
import logging
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


class LlamaCppClient:
    """HTTP client for communicating with local llama.cpp REST API server (OpenAI / native completion format) for Qwen2.5-3B-Instruct."""

    def __init__(self, base_url: Optional[str] = None):
        if not base_url:
            base_url = os.environ.get("LLAMACPP_BASE_URL", os.environ.get("LLAMA_SERVER_URL", "http://localhost:8080"))
        self.base_url = base_url.rstrip("/")
        self.model_manager = LlamaCppModelManager(base_url=self.base_url)
        self.last_metrics: Dict[str, Any] = {}

    def ensure_model_loaded(self, timeout: int = 60) -> Tuple[bool, str]:
        """Delegate to LlamaCppModelManager to guarantee llama-server is healthy."""
        return self.model_manager.ensure_qwen25_loaded(timeout=timeout)

    def check_availability(self, model_name: str = TRANSLATION_MODEL) -> Tuple[bool, str]:
        """Check if llama.cpp server is reachable."""
        healthy, msg = self.model_manager.check_health()
        if not healthy:
            return False, f"llama.cpp server is not running at {self.base_url}: {msg}"
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
        Sends a multi-turn chat completion request to llama.cpp REST API.
        Uses OpenAI compatible /v1/chat/completions endpoint.
        """
        if model and not model_name:
            model_name = model

        if system:
            messages = [{"role": "system", "content": system}] + list(messages)

        if not options:
            options = {}
        if kwargs:
            options.update(kwargs)

        temperature = options.get("temperature", 0.1)
        top_p = options.get("top_p", 0.9)
        max_tokens = options.get("max_tokens", options.get("num_predict", 1024))

        # Try /v1/chat/completions
        url = f"{self.base_url}/v1/chat/completions"
        payload = {
            "model": model_name,
            "messages": messages,
            "temperature": temperature,
            "top_p": top_p,
            "max_tokens": max_tokens,
            "stream": False
        }

        data_bytes = json.dumps(payload).encode("utf-8")
        req = urllib.request.Request(
            url,
            data=data_bytes,
            headers={"Content-Type": "application/json", "User-Agent": "AutoDubStudio"}
        )

        t0 = time.time()
        try:
            with urllib.request.urlopen(req, timeout=timeout) as response:
                if response.status != 200:
                    raise TranslationFailedError(f"llama.cpp returned HTTP status {response.status}")
                res_data = json.loads(response.read().decode("utf-8"))
        except urllib.error.URLError as e:
            if isinstance(e.reason, socket_timeout_types):
                raise LlamaCppTimeoutError(f"llama.cpp chat request timed out after {timeout} seconds.")
            # Fallback to native /completion endpoint if /v1/chat/completions fails
            return self._fallback_native_completion(messages, options, timeout)
        except socket_timeout_types:
            raise LlamaCppTimeoutError(f"llama.cpp chat request timed out after {timeout} seconds.")
        except Exception as e:
            if "llama.cpp" in str(e) or "TranslationFailedError" in str(type(e)):
                raise
            # Try native completion fallback
            try:
                return self._fallback_native_completion(messages, options, timeout)
            except Exception:
                raise LlamaCppUnavailableError(f"Failed to communicate with llama.cpp server at {self.base_url}: {e}")

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
        messages = []
        if system:
            messages.append({"role": "system", "content": system})
        messages.append({"role": "user", "content": prompt})

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
