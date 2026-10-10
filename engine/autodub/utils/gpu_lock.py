import threading
import logging

logger = logging.getLogger("autodub")

class GpuLockManager:
    """Sequential Resource Ownership Lock for GPU inference workloads (Whisper / Ollama)."""
    _instance = None
    _lock = threading.Lock()
    _gpu_owner_lock = threading.Lock()
    _current_owner = None

    def __new__(cls):
        with cls._lock:
            if cls._instance is None:
                cls._instance = super(GpuLockManager, cls).__new__(cls)
            return cls._instance

    def acquire_gpu(self, owner_name: str, timeout: float = 300.0) -> bool:
        """Acquire exclusive GPU ownership. Blocks until available or timed out."""
        logger.info(f"[{owner_name}] Requesting exclusive GPU ownership...")
        acquired = self._gpu_owner_lock.acquire(timeout=timeout)
        if acquired:
            self._current_owner = owner_name
            logger.info(f"[{owner_name}] GPU lock acquired successfully.")
            return True
        else:
            logger.error(f"[{owner_name}] Failed to acquire GPU lock after {timeout} seconds. Current owner: {self._current_owner}")
            return False

    def release_gpu(self, owner_name: str):
        """Release GPU ownership lock."""
        if self._current_owner == owner_name:
            self._current_owner = None
            try:
                self._gpu_owner_lock.release()
                logger.info(f"[{owner_name}] GPU lock released successfully.")
            except RuntimeError:
                pass
        else:
            logger.warning(f"[{owner_name}] Attempted to release GPU lock but current owner is {self._current_owner}")

gpu_lock_manager = GpuLockManager()
