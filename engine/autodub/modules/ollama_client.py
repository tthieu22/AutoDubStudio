import json
import os
import time
import urllib.request
import urllib.error
import socket
from typing import Tuple, Optional
from autodub.config import DEFAULT_TRANSLATION_MODEL
from autodub.exceptions import (
    TranslationFailedError,
    OllamaUnavailableError,
    OllamaTimeoutError
)

socket_timeout_types = (socket.timeout, TimeoutError)

class OllamaClient:
    """HTTP client for communicating with local Ollama REST API server."""
    def __init__(self, base_url: Optional[str] = None):
        if not base_url:
            base_url = os.environ.get("OLLAMA_BASE_URL", "http://localhost:11434")
        self.base_url = base_url.rstrip("/")

    def check_availability(self, model_name: str = DEFAULT_TRANSLATION_MODEL) -> Tuple[bool, str]:
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

    def generate(
        self,
        prompt: str,
        system: Optional[str] = None,
        model: str = DEFAULT_TRANSLATION_MODEL,
        temperature: float = 0.15,
        format_json: bool = False,
        timeout: int = 120
    ) -> str:
        """Call Ollama /api/generate REST endpoint synchronously with fixed low temperature."""
        url = f"{self.base_url}/api/generate"
        payload = {
            "model": model,
            "prompt": prompt,
            "stream": False,
            "options": {
                "temperature": temperature
            }
        }
        # Note: Ollama HTTP API hangs/times out when format="json" option is sent for qwen3 models.
        # Prompt-based JSON instruction is used for qwen3 instead.
        if format_json and not model.startswith("qwen3"):
            payload["format"] = "json"
        if system:
            payload["system"] = system

        # Automatic retry loop (max 3 retries for transient Ollama timeouts or format quirks)
        for attempt in range(1, 4):
            try:
                req = urllib.request.Request(
                    url,
                    data=json.dumps(payload).encode("utf-8"),
                    headers={"Content-Type": "application/json", "User-Agent": "AutoDubStudio"}
                )
                with urllib.request.urlopen(req, timeout=timeout) as resp:
                    result = json.loads(resp.read().decode("utf-8"))
                    response_text = result.get("response", "").strip()

                    # If format_json produced an empty response, retry without format="json"
                    if not response_text and format_json:
                        payload.pop("format", None)
                        req_retry = urllib.request.Request(
                            url,
                            data=json.dumps(payload).encode("utf-8"),
                            headers={"Content-Type": "application/json", "User-Agent": "AutoDubStudio"}
                        )
                        with urllib.request.urlopen(req_retry, timeout=timeout) as resp_retry:
                            result_retry = json.loads(resp_retry.read().decode("utf-8"))
                            response_text = result_retry.get("response", "").strip()

                    return response_text
            except (urllib.error.URLError, socket.timeout, TimeoutError, Exception) as e:
                print(f"Ollama request attempt #{attempt} timeout/error: {e}. Retrying in 2 seconds...", flush=True)
                time.sleep(2)
                if attempt == 3:
                    if "timed out" in str(e).lower() or isinstance(e, (socket.timeout, TimeoutError)):
                        raise OllamaTimeoutError(f"Ollama generate request timed out after {timeout} seconds.")
                    raise TranslationFailedError(f"Ollama API request failed: {e}")
