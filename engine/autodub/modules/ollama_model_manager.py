import json
import logging
import os
import threading
import time
import urllib.request
import urllib.error
from typing import Dict, Any, List, Optional, Tuple

from autodub.config import TRANSLATION_MODEL
from autodub.exceptions import (
    OllamaUnavailableError,
    OllamaModelNotFoundError,
    TranslationFailedError
)

logger = logging.getLogger("autodub")

# Exclusive Model Lifecycle Lock
_MODEL_LIFECYCLE_LOCK = threading.RLock()


class OllamaModelManager:
    """Exclusive Ollama Model Lifecycle Manager for AutoDubStudio.
    
    Guarantees that on memory-constrained GPUs (e.g. NVIDIA GTX 1650 Ti 4GB VRAM):
    1. Exactly ONE Ollama model is loaded at any given time (qwen3:4b ONLY).
    2. Any conflicting/other models in VRAM are systematically unloaded before loading qwen3:4b.
    3. Model warmup uses keep_alive="1h" to maintain low-latency inference throughout the pipeline.
    4. All model lifecycle operations are synchronized via a thread-safe re-entrant lock.
    """

    DEFAULT_TARGET_MODEL = TRANSLATION_MODEL

    def __init__(self, base_url: Optional[str] = None):
        if not base_url:
            base_url = os.environ.get("OLLAMA_BASE_URL", "http://localhost:11434")
        self.base_url = base_url.rstrip("/")

    def get_loaded_models(self) -> List[Dict[str, Any]]:
        """Query Ollama GET /api/ps to retrieve all currently loaded models in VRAM/RAM."""
        url = f"{self.base_url}/api/ps"
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "AutoDubStudio"})
            with urllib.request.urlopen(req, timeout=5) as response:
                if response.status == 200:
                    data = json.loads(response.read().decode("utf-8"))
                    return data.get("models", [])
        except Exception as e:
            logger.debug(f"[MODEL_MANAGER] Failed to fetch /api/ps: {e}")
        return []

    def get_installed_models(self) -> List[str]:
        """Query Ollama GET /api/tags to list all installed model names."""
        url = f"{self.base_url}/api/tags"
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "AutoDubStudio"})
            with urllib.request.urlopen(req, timeout=5) as response:
                if response.status == 200:
                    data = json.loads(response.read().decode("utf-8"))
                    models = data.get("models", [])
                    names = []
                    for m in models:
                        if "name" in m:
                            names.append(m["name"])
                        if "model" in m and m["model"] not in names:
                            names.append(m["model"])
                    return names
        except Exception as e:
            logger.debug(f"[MODEL_MANAGER] Failed to fetch /api/tags: {e}")
        return []

    def is_model_installed(self, model_name: str = DEFAULT_TARGET_MODEL) -> bool:
        """Verify whether the requested model is installed in Ollama."""
        installed = self.get_installed_models()
        target_base = model_name.split(":")[0]
        for item in installed:
            if item == model_name or item.startswith(f"{model_name}:"):
                return True
            if item == target_base or item.startswith(f"{target_base}:"):
                return True
        return False

    def unload_model(self, model_name: str) -> bool:
        """Unload a specific model from VRAM by sending keep_alive=0 to /api/generate."""
        url = f"{self.base_url}/api/generate"
        payload = {
            "model": model_name,
            "prompt": "",
            "keep_alive": 0
        }
        try:
            req = urllib.request.Request(
                url,
                data=json.dumps(payload).encode("utf-8"),
                headers={"Content-Type": "application/json", "User-Agent": "AutoDubStudio"}
            )
            with urllib.request.urlopen(req, timeout=10) as resp:
                if resp.status == 200:
                    logger.info(f"[MODEL_MANAGER] Sent unload signal (keep_alive=0) for model '{model_name}'")
                    return True
        except Exception as e:
            logger.warning(f"[MODEL_MANAGER] Unload request failed for model '{model_name}': {e}")
        return False

    def unload_other_models(self, target_model: str = DEFAULT_TARGET_MODEL, wait_timeout: float = 10.0) -> List[str]:
        """Check all currently loaded models. If any model other than target_model is loaded, unload it."""
        unloaded_list = []
        loaded_models = self.get_loaded_models()
        target_base = target_model.split(":")[0]

        for m in loaded_models:
            m_name = m.get("name", "") or m.get("model", "")
            if not m_name:
                continue
            # If loaded model does not match target model, unload it
            if m_name != target_model and not m_name.startswith(f"{target_base}:") and m_name != target_base:
                logger.warning(f"[MODEL_MANAGER] Foreign model '{m_name}' detected in VRAM. Unloading to prevent VRAM contention...")
                self.unload_model(m_name)
                unloaded_list.append(m_name)

        if unloaded_list:
            # Poll /api/ps until all unloaded models are gone
            t0 = time.time()
            while time.time() - t0 < wait_timeout:
                current_loaded = self.get_loaded_models()
                current_names = [m.get("name", "") for m in current_loaded]
                if not any(unloaded in current_names for unloaded in unloaded_list):
                    logger.info(f"[MODEL_MANAGER] Confirmed unload of foreign models: {unloaded_list}")
                    break
                time.sleep(0.5)

        return unloaded_list

    def is_qwen3_loaded(self) -> bool:
        """Check if qwen3:4b is currently loaded in Ollama VRAM."""
        loaded = self.get_loaded_models()
        for m in loaded:
            m_name = m.get("name", "") or m.get("model", "")
            if "qwen3" in m_name:
                return True
        return False

    def verify_exclusive_model(self, target_model: str = DEFAULT_TARGET_MODEL) -> Tuple[bool, str]:
        """Verify that ONLY the target model is loaded in Ollama, and no other models exist in VRAM."""
        loaded = self.get_loaded_models()
        if not loaded:
            return False, "No models currently loaded in Ollama."

        target_base = target_model.split(":")[0]
        loaded_names = [m.get("name", "") or m.get("model", "") for m in loaded]

        for name in loaded_names:
            if name != target_model and not name.startswith(f"{target_base}:") and name != target_base:
                return False, f"MODEL_CONFLICT_DETECTED: Multiple/foreign models loaded in VRAM ({loaded_names}). Expected exclusive: {target_model}"

        has_target = any(name == target_model or name.startswith(f"{target_base}:") or name == target_base for name in loaded_names)
        if not has_target:
            return False, f"Target model '{target_model}' is not among loaded models: {loaded_names}"

        return True, f"Exclusive model verified: {target_model} (Total loaded: {len(loaded_names)})"

    def ensure_qwen3_loaded(self, timeout: int = 60) -> Tuple[bool, str]:
        """Thread-safe orchestration to ensure qwen3:4b is exclusively loaded into VRAM.
        
        Execution steps:
        1. Acquire model lifecycle lock.
        2. Verify Ollama server connectivity.
        3. Check qwen3:4b installation.
        4. Detect and unload any other models.
        5. Warm up qwen3:4b with keep_alive="1h".
        6. Verify exclusive model residency in VRAM.
        7. Release lock.
        """
        with _MODEL_LIFECYCLE_LOCK:
            logger.info(f"[MODEL_MANAGER] Ensuring exclusive loaded model: '{self.DEFAULT_TARGET_MODEL}'...")

            # 1. Check Ollama connectivity
            installed = self.get_installed_models()
            if not installed and not self.is_model_installed(self.DEFAULT_TARGET_MODEL):
                # Verify if server is unreachable
                url = f"{self.base_url}/api/tags"
                try:
                    req = urllib.request.Request(url, headers={"User-Agent": "AutoDubStudio"})
                    urllib.request.urlopen(req, timeout=5)
                except Exception as e:
                    err_msg = f"Ollama is not running at {self.base_url}"
                    logger.error(f"[MODEL_MANAGER] {err_msg}")
                    return False, err_msg

                err_msg = f"Ollama model '{self.DEFAULT_TARGET_MODEL}' is not installed."
                logger.error(f"[MODEL_MANAGER] {err_msg}")
                return False, err_msg

            if not self.is_model_installed(self.DEFAULT_TARGET_MODEL):
                err_msg = f"Ollama model '{self.DEFAULT_TARGET_MODEL}' is not installed."
                logger.error(f"[MODEL_MANAGER] {err_msg}")
                return False, err_msg

            # 2. Unload any foreign models
            self.unload_other_models(target_model=self.DEFAULT_TARGET_MODEL)

            # 3. Check if target model is already exclusively loaded
            is_exclusive, _ = self.verify_exclusive_model(target_model=self.DEFAULT_TARGET_MODEL)
            if is_exclusive:
                logger.info(f"[MODEL_MANAGER] '{self.DEFAULT_TARGET_MODEL}' is already exclusively loaded and active in VRAM.")
                return True, ""

            # 4. Warm-up load qwen3:4b into VRAM with keep_alive="1h"
            logger.info(f"[MODEL_MANAGER] Loading '{self.DEFAULT_TARGET_MODEL}' into VRAM (keep_alive=1h)...")
            warmup_url = f"{self.base_url}/api/generate"
            warmup_payload = {
                "model": self.DEFAULT_TARGET_MODEL,
                "prompt": "",
                "stream": False,
                "keep_alive": "1h"
            }
            try:
                req = urllib.request.Request(
                    warmup_url,
                    data=json.dumps(warmup_payload).encode("utf-8"),
                    headers={"Content-Type": "application/json", "User-Agent": "AutoDubStudio"}
                )
                with urllib.request.urlopen(req, timeout=timeout) as resp:
                    resp.read()
            except Exception as e:
                err_msg = f"Failed to warm up and load '{self.DEFAULT_TARGET_MODEL}': {e}"
                logger.error(f"[MODEL_MANAGER] {err_msg}")
                return False, err_msg

            # 5. Final exclusivity verification
            verified, verify_msg = self.verify_exclusive_model(target_model=self.DEFAULT_TARGET_MODEL)
            if not verified:
                logger.warning(f"[MODEL_MANAGER] Post-load verification notice: {verify_msg}")
                # Allow a brief grace period if Ollama is finalizing registration
                time.sleep(1.0)
                verified, verify_msg = self.verify_exclusive_model(target_model=self.DEFAULT_TARGET_MODEL)

            if verified:
                logger.info(f"[MODEL_MANAGER] SUCCESS: {verify_msg}")
                return True, ""
            else:
                logger.error(f"[MODEL_MANAGER] Exclusive load verification failed: {verify_msg}")
                return False, verify_msg

    def get_runtime_status(self) -> Dict[str, Any]:
        """Return runtime status regarding model residency and VRAM distribution."""
        loaded_models = self.get_loaded_models()
        is_exclusive, status_msg = self.verify_exclusive_model(self.DEFAULT_TARGET_MODEL)
        
        vram_total_mb = 0.0
        details = []
        for m in loaded_models:
            size_vram = m.get("size_vram", 0) / (1024 * 1024)
            vram_total_mb += size_vram
            details.append({
                "name": m.get("name") or m.get("model"),
                "size_vram_mb": round(size_vram, 2),
                "size_mb": round(m.get("size", 0) / (1024 * 1024), 2),
                "processor": m.get("processor", "Unknown"),
                "expires_at": m.get("expires_at")
            })

        return {
            "target_model": self.DEFAULT_TARGET_MODEL,
            "is_exclusive": is_exclusive,
            "status_message": status_msg,
            "loaded_model_count": len(loaded_models),
            "total_vram_used_mb": round(vram_total_mb, 2),
            "models": details
        }
