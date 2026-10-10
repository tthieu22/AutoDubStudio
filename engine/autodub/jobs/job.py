import time
import uuid
from dataclasses import dataclass, asdict, field
from typing import Dict, Any, Optional

from autodub.jobs.job_state import JobState, validate_job_state_transition


@dataclass
class Job:
    job_id: str
    project_id: str
    input_path: str
    output_path: str
    status: str = JobState.PENDING.value
    current_stage: str = "INGEST"
    progress: float = 0.0
    created_at: float = field(default_factory=time.time)
    started_at: Optional[float] = None
    completed_at: Optional[float] = None
    updated_at: float = field(default_factory=time.time)
    retry_count: int = 0
    max_retries: int = 3
    priority: int = 5
    error_code: Optional[str] = None
    error_message: Optional[str] = None
    config_hash: str = ""
    pipeline_version: str = "9.0"
    worker_id: Optional[str] = None

    @classmethod
    def create(
        cls,
        project_id: str,
        input_path: str,
        output_path: str,
        *,
        job_id: Optional[str] = None,
        config_hash: str = "",
        priority: int = 5,
        max_retries: int = 3
    ) -> "Job":
        now = time.time()
        j_id = job_id or f"job_{uuid.uuid4().hex[:12]}"
        return cls(
            job_id=j_id,
            project_id=project_id,
            input_path=str(input_path),
            output_path=str(output_path),
            status=JobState.PENDING.value,
            current_stage="INGEST",
            progress=0.0,
            created_at=now,
            updated_at=now,
            priority=priority,
            max_retries=max_retries,
            config_hash=config_hash
        )

    def transition_to(self, new_status: str, *, force: bool = False, error_message: Optional[str] = None) -> None:
        validate_job_state_transition(self.status, new_status, force=force)
        self.status = new_status.upper()
        self.updated_at = time.time()

        if self.status == JobState.RUNNING.value and self.started_at is None:
            self.started_at = self.updated_at

        if self.status in (JobState.COMPLETED.value, JobState.FAILED.value, JobState.CANCELLED.value):
            self.completed_at = self.updated_at

        if error_message:
            self.error_message = error_message

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Job":
        data = data or {}
        return cls(
            job_id=data.get("job_id", ""),
            project_id=data.get("project_id", ""),
            input_path=data.get("input_path", ""),
            output_path=data.get("output_path", ""),
            status=data.get("status", JobState.PENDING.value),
            current_stage=data.get("current_stage", "INGEST"),
            progress=float(data.get("progress", 0.0)),
            created_at=float(data.get("created_at", time.time())),
            started_at=float(data["started_at"]) if data.get("started_at") is not None else None,
            completed_at=float(data["completed_at"]) if data.get("completed_at") is not None else None,
            updated_at=float(data.get("updated_at", time.time())),
            retry_count=int(data.get("retry_count", 0)),
            max_retries=int(data.get("max_retries", 3)),
            priority=int(data.get("priority", 5)),
            error_code=data.get("error_code"),
            error_message=data.get("error_message"),
            config_hash=data.get("config_hash", ""),
            pipeline_version=data.get("pipeline_version", "9.0"),
            worker_id=data.get("worker_id")
        )
