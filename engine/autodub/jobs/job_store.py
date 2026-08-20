import json
import sqlite3
import threading
import time
from pathlib import Path
from typing import Dict, Any, List, Optional

from autodub.config import BASE_DIR
from autodub.jobs.job import Job
from autodub.exceptions import JobNotFoundError, JobAlreadyExistsError, JobError


class JobStore:
    """Thread-safe SQLite persistent store for AutoDubStudio Jobs & Lifecycle Events."""

    def __init__(self, db_path: Optional[Path] = None):
        if db_path is None:
            db_dir = BASE_DIR / ".autodub"
            db_dir.mkdir(parents=True, exist_ok=True)
            self.db_path = db_dir / "jobs.db"
        else:
            self.db_path = Path(db_path)
            self.db_path.parent.mkdir(parents=True, exist_ok=True)

        self._lock = threading.Lock()
        self.init_db()

    def _get_connection(self) -> sqlite3.Connection:
        conn = sqlite3.connect(str(self.db_path), timeout=10.0)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA journal_mode=WAL;")
        conn.execute("PRAGMA busy_timeout=5000;")
        conn.execute("PRAGMA synchronous=NORMAL;")
        return conn

    def init_db(self) -> None:
        with self._lock:
            conn = self._get_connection()
            try:
                with conn:
                    conn.execute("""
                        CREATE TABLE IF NOT EXISTS jobs (
                            job_id TEXT PRIMARY KEY,
                            project_id TEXT NOT NULL,
                            input_path TEXT NOT NULL,
                            output_path TEXT NOT NULL,
                            status TEXT NOT NULL,
                            current_stage TEXT NOT NULL,
                            progress REAL NOT NULL,
                            created_at REAL NOT NULL,
                            started_at REAL,
                            completed_at REAL,
                            updated_at REAL NOT NULL,
                            retry_count INTEGER NOT NULL,
                            max_retries INTEGER NOT NULL,
                            priority INTEGER NOT NULL,
                            error_code TEXT,
                            error_message TEXT,
                            config_hash TEXT NOT NULL,
                            pipeline_version TEXT NOT NULL,
                            worker_id TEXT
                        );
                    """)
                    conn.execute("CREATE INDEX IF NOT EXISTS idx_jobs_status ON jobs(status);")
                    conn.execute("CREATE INDEX IF NOT EXISTS idx_jobs_priority ON jobs(priority, created_at);")
                    conn.execute("CREATE INDEX IF NOT EXISTS idx_jobs_fingerprint ON jobs(input_path, config_hash);")

                    conn.execute("""
                        CREATE TABLE IF NOT EXISTS job_events (
                            event_id INTEGER PRIMARY KEY AUTOINCREMENT,
                            job_id TEXT NOT NULL,
                            event_type TEXT NOT NULL,
                            stage TEXT NOT NULL,
                            timestamp REAL NOT NULL,
                            message TEXT,
                            metadata TEXT,
                            FOREIGN KEY(job_id) REFERENCES jobs(job_id) ON DELETE CASCADE
                        );
                    """)
                    conn.execute("CREATE INDEX IF NOT EXISTS idx_events_job ON job_events(job_id);")
            finally:
                conn.close()

    def save_job(self, job: Job, *, create_only: bool = False) -> Job:
        with self._lock:
            conn = self._get_connection()
            try:
                with conn:
                    existing = conn.execute("SELECT job_id FROM jobs WHERE job_id = ?", (job.job_id,)).fetchone()
                    if create_only and existing:
                        raise JobAlreadyExistsError(f"Job with ID '{job.job_id}' already exists.")

                    conn.execute("""
                        INSERT INTO jobs (
                            job_id, project_id, input_path, output_path, status, current_stage,
                            progress, created_at, started_at, completed_at, updated_at,
                            retry_count, max_retries, priority, error_code, error_message,
                            config_hash, pipeline_version, worker_id
                        ) VALUES (
                            ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?
                        ) ON CONFLICT(job_id) DO UPDATE SET
                            project_id=excluded.project_id,
                            input_path=excluded.input_path,
                            output_path=excluded.output_path,
                            status=excluded.status,
                            current_stage=excluded.current_stage,
                            progress=excluded.progress,
                            started_at=excluded.started_at,
                            completed_at=excluded.completed_at,
                            updated_at=excluded.updated_at,
                            retry_count=excluded.retry_count,
                            max_retries=excluded.max_retries,
                            priority=excluded.priority,
                            error_code=excluded.error_code,
                            error_message=excluded.error_message,
                            config_hash=excluded.config_hash,
                            pipeline_version=excluded.pipeline_version,
                            worker_id=excluded.worker_id;
                    """, (
                        job.job_id, job.project_id, job.input_path, job.output_path, job.status,
                        job.current_stage, job.progress, job.created_at, job.started_at, job.completed_at,
                        job.updated_at, job.retry_count, job.max_retries, job.priority, job.error_code,
                        job.error_message, job.config_hash, job.pipeline_version, job.worker_id
                    ))
            finally:
                conn.close()
        return job

    def get_job(self, job_id: str) -> Optional[Job]:
        with self._lock:
            conn = self._get_connection()
            try:
                row = conn.execute("SELECT * FROM jobs WHERE job_id = ?", (job_id,)).fetchone()
                if not row:
                    return None
                return Job.from_dict(dict(row))
            finally:
                conn.close()

    def find_job_by_fingerprint(self, input_path: str, config_hash: str) -> Optional[Job]:
        with self._lock:
            conn = self._get_connection()
            try:
                row = conn.execute(
                    "SELECT * FROM jobs WHERE input_path = ? AND config_hash = ? ORDER BY created_at DESC LIMIT 1",
                    (str(input_path), config_hash)
                ).fetchone()
                if not row:
                    return None
                return Job.from_dict(dict(row))
            finally:
                conn.close()

    def list_jobs(self, status: Optional[str] = None, limit: int = 100) -> List[Job]:
        with self._lock:
            conn = self._get_connection()
            try:
                if status:
                    rows = conn.execute(
                        "SELECT * FROM jobs WHERE UPPER(status) = UPPER(?) ORDER BY priority DESC, created_at ASC LIMIT ?",
                        (status, limit)
                    ).fetchall()
                else:
                    rows = conn.execute(
                        "SELECT * FROM jobs ORDER BY priority DESC, created_at ASC LIMIT ?",
                        (limit,)
                    ).fetchall()
                return [Job.from_dict(dict(r)) for r in rows]
            finally:
                conn.close()

    def delete_job(self, job_id: str) -> bool:
        with self._lock:
            conn = self._get_connection()
            try:
                with conn:
                    res = conn.execute("DELETE FROM jobs WHERE job_id = ?", (job_id,))
                    return res.rowcount > 0
            finally:
                conn.close()

    def log_event(
        self,
        job_id: str,
        event_type: str,
        stage: str,
        message: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> None:
        with self._lock:
            conn = self._get_connection()
            try:
                with conn:
                    meta_str = json.dumps(metadata) if metadata else None
                    conn.execute("""
                        INSERT INTO job_events (job_id, event_type, stage, timestamp, message, metadata)
                        VALUES (?, ?, ?, ?, ?, ?);
                    """, (job_id, event_type, stage, time.time(), message, meta_str))
            finally:
                conn.close()

    def get_job_events(self, job_id: str) -> List[Dict[str, Any]]:
        with self._lock:
            conn = self._get_connection()
            try:
                rows = conn.execute(
                    "SELECT * FROM job_events WHERE job_id = ? ORDER BY timestamp ASC",
                    (job_id,)
                ).fetchall()
                results = []
                for r in rows:
                    item = dict(r)
                    if item.get("metadata"):
                        try:
                            item["metadata"] = json.loads(item["metadata"])
                        except Exception:
                            pass
                    results.append(item)
                return results
            finally:
                conn.close()
