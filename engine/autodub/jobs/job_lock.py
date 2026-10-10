import json
import os
import time
from pathlib import Path
from typing import Optional
from autodub.exceptions import JobLockError


class JobLock:
    """File-system based atomic lock manager for concurrent job execution."""

    def __init__(self, lock_dir: Optional[Path] = None, stale_timeout_sec: float = 120.0):
        self.lock_dir = Path(lock_dir) if lock_dir else Path.cwd() / ".autodub" / "locks"
        self.lock_dir.mkdir(parents=True, exist_ok=True)
        self.stale_timeout_sec = stale_timeout_sec

    def _get_lock_file(self, job_id: str) -> Path:
        safe_id = job_id.replace("/", "_").replace("\\", "_")
        return self.lock_dir / f"{safe_id}.lock"

    def acquire(self, job_id: str, worker_id: str, force: bool = False) -> bool:
        lock_file = self._get_lock_file(job_id)

        if lock_file.exists():
            try:

                with open(lock_file, "r", encoding="utf-8") as f:
                    data = json.load(f)
                existing_worker = data.get("worker_id")
                updated_at = data.get("updated_at", 0.0)

                if existing_worker == worker_id:
                    # Re-acquire/heartbeat by same worker
                    self.heartbeat(job_id, worker_id)
                    return True

                # Check stale
                if time.time() - updated_at > self.stale_timeout_sec or force:
                    lock_file.unlink(missing_ok=True)
                else:
                    return False
            except Exception:
                lock_file.unlink(missing_ok=True)

        try:

            lock_info = {
                "job_id": job_id,
                "worker_id": worker_id,
                "acquired_at": time.time(),
                "updated_at": time.time(),
                "pid": os.getpid()
            }
            tmp_lock = lock_file.with_suffix(".tmp")
            with open(tmp_lock, "w", encoding="utf-8") as f:
                json.dump(lock_info, f)

            os.replace(tmp_lock, lock_file)
            return True
        except Exception as e:
            raise JobLockError(f"Failed to acquire lock for job '{job_id}': {e}")

    def heartbeat(self, job_id: str, worker_id: str) -> None:
        lock_file = self._get_lock_file(job_id)
        if not lock_file.exists():
            return
        try:

            with open(lock_file, "r", encoding="utf-8") as f:
                data = json.load(f)

            if data.get("worker_id") == worker_id:
                data["updated_at"] = time.time()
                tmp_lock = lock_file.with_suffix(".tmp")
                with open(tmp_lock, "w", encoding="utf-8") as f:
                    json.dump(data, f)
                os.replace(tmp_lock, lock_file)
        except Exception:
            pass

    def release(self, job_id: str, worker_id: str, force: bool = False) -> bool:
        lock_file = self._get_lock_file(job_id)
        if not lock_file.exists():
            return True

        try:

            with open(lock_file, "r", encoding="utf-8") as f:
                data = json.load(f)

            if data.get("worker_id") == worker_id or force:
                lock_file.unlink(missing_ok=True)
                return True
            return False
        except Exception:
            lock_file.unlink(missing_ok=True)
            return True

    def is_locked(self, job_id: str) -> bool:
        lock_file = self._get_lock_file(job_id)
        if not lock_file.exists():
            return False
        try:

            with open(lock_file, "r", encoding="utf-8") as f:
                data = json.load(f)
            updated_at = data.get("updated_at", 0.0)
            if time.time() - updated_at > self.stale_timeout_sec:
                return False
            return True
        except Exception:
            return False
