import atexit
import json
import logging
import os
import subprocess
import threading
import time
import urllib.request
import urllib.error
from pathlib import Path
from typing import List, Optional, Tuple

from autodub.config import BASE_DIR, TRANSLATION_MODEL
from autodub.exceptions import LlamaCppUnavailableError

logger = logging.getLogger("autodub")

_MODEL_LIFECYCLE_LOCK = threading.RLock()


class LlamaCppModelManager:
    """Exclusive LlamaCpp Model Lifecycle, Connection, and Auto-Spawn Manager for AutoDubStudio.

    Guarantees that:
    1. Automatic process lifecycle: Spawns llama-server.exe on demand if not running.
    2. Automatically terminates llama-server.exe when translation stage finishes or script exits.
    3. Thread-safe execution under hardware VRAM constraints (e.g., GTX 1650 Ti 4GB VRAM).
    """

    DEFAULT_TARGET_MODEL = TRANSLATION_MODEL
    _spawned_process: Optional[subprocess.Popen] = None
    _is_atexit_registered = False

    def __init__(self, base_url: Optional[str] = None):
        if not base_url:
            base_url = os.environ.get("LLAMACPP_BASE_URL", os.environ.get("LLAMA_SERVER_URL", "http://localhost:8080"))
        self.base_url = base_url.rstrip("/")
        
        if not LlamaCppModelManager._is_atexit_registered:
            atexit.register(self.stop_server_auto)
            LlamaCppModelManager._is_atexit_registered = True

    def check_health(self) -> Tuple[bool, str]:
        """Check if llama.cpp server is running and healthy by querying GET /health or GET /v1/models."""
        # 1. Try GET /health (llama.cpp native endpoint)
        health_url = f"{self.base_url}/health"
        try:
            req = urllib.request.Request(health_url, headers={"User-Agent": "AutoDubStudio"})
            with urllib.request.urlopen(req, timeout=3) as resp:
                if resp.status == 200:
                    data = json.loads(resp.read().decode("utf-8"))
                    if data.get("status") in ("ok", "healthy"):
                        return True, "llama.cpp server is healthy and model is loaded."
                    elif data.get("error", {}).get("code") == 503:
                        return False, "llama.cpp server is currently loading model tensors..."
                    return True, f"llama.cpp server response: {data}"
        except Exception:
            pass

        # 2. Try GET /v1/models (OpenAI compatible endpoint)
        models_url = f"{self.base_url}/v1/models"
        try:
            req = urllib.request.Request(models_url, headers={"User-Agent": "AutoDubStudio"})
            with urllib.request.urlopen(req, timeout=3) as resp:
                if resp.status == 200:
                    return True, "llama.cpp server /v1/models is accessible."
        except Exception as e:
            return False, f"llama.cpp server is not running or unreachable at {self.base_url}: {e}"

        return False, f"llama.cpp server at {self.base_url} returned non-200 status."

    def start_server_auto(self, model_filename: str = "qwen2.5-3b-instruct-q4_k_m.gguf", port: int = 8080, gpu_layers: int = 99, timeout: int = 45) -> bool:
        """Automatically spawns llama-server.exe if not already running on port."""
        with _MODEL_LIFECYCLE_LOCK:
            healthy, msg = self.check_health()
            if healthy:
                logger.info(f"[LLAMACPP_MANAGER] llama-server is already active at {self.base_url}")
                return True

            logger.info(f"[LLAMACPP_MANAGER] Auto-spawning llama-server.exe for model '{model_filename}' on GPU (port {port})...")
            
            # Locate binary executable
            exe_path = BASE_DIR / "runtime" / "llama.cpp" / ("llama-server.exe" if os.name == "nt" else "llama-server")
            if not exe_path.exists():
                # Fallback to PATH lookup
                exe_path = Path("llama-server.exe" if os.name == "nt" else "llama-server")

            # Locate GGUF model file
            model_path = BASE_DIR / "models" / "llm" / model_filename
            if not model_path.exists():
                raise LlamaCppUnavailableError(f"Model file missing: {model_path}. Please place {model_filename} in models/llm/")

            cmd = [
                str(exe_path),
                "-m", str(model_path),
                "-ngl", str(gpu_layers),
                "--port", str(port)
            ]

            try:
                proc = subprocess.Popen(
                    cmd,
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                    creationflags=subprocess.CREATE_NO_WINDOW if os.name == "nt" else 0
                )
                LlamaCppModelManager._spawned_process = proc
                logger.info(f"[LLAMACPP_MANAGER] Spawned llama-server.exe (PID: {proc.pid}). Waiting for initialization...")

                # Poll health until ready
                t0 = time.time()
                while time.time() - t0 < timeout:
                    healthy, msg = self.check_health()
                    if healthy:
                        logger.info(f"[LLAMACPP_MANAGER] llama-server.exe PID {proc.pid} is 100% READY at {self.base_url}!")
                        return True
                    time.sleep(1.5)

                raise LlamaCppUnavailableError(f"llama-server.exe failed to become ready within {timeout}s: {msg}")
            except Exception as e:
                self.stop_server_auto()
                raise LlamaCppUnavailableError(f"Failed to auto-spawn llama-server.exe: {e}")

    def stop_server_auto(self):
        """Terminates auto-spawned llama-server.exe process and releases GPU VRAM."""
        with _MODEL_LIFECYCLE_LOCK:
            proc = LlamaCppModelManager._spawned_process
            if proc is not None:
                try:
                    logger.info(f"[LLAMACPP_MANAGER] Auto-terminating spawned llama-server.exe (PID: {proc.pid}) & releasing GPU VRAM...")
                    proc.terminate()
                    proc.wait(timeout=5)
                except Exception:
                    try:
                        proc.kill()
                    except Exception:
                        pass
                finally:
                    LlamaCppModelManager._spawned_process = None
                    logger.info("[LLAMACPP_MANAGER] llama-server.exe process terminated. GPU VRAM released.")

    def ensure_qwen25_loaded(self, model_name: str = DEFAULT_TARGET_MODEL, timeout: int = 60) -> Tuple[bool, str]:
        """Ensure llama.cpp server is active and Qwen2.5-3B model is ready for inference (auto-spawns if needed)."""
        with _MODEL_LIFECYCLE_LOCK:
            healthy, _ = self.check_health()
            if not healthy:
                self.start_server_auto(timeout=timeout)
            return True, "Qwen2.5-3B model ready on llama.cpp CUDA"

    def ensure_qwen3_loaded(self, timeout: int = 60) -> Tuple[bool, str]:
        """Alias for backward compatibility."""
        return self.ensure_qwen25_loaded(timeout=timeout)


# Alias for backward compatibility
OllamaModelManager = LlamaCppModelManager
