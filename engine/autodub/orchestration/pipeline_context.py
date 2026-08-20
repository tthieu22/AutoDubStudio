from dataclasses import dataclass
from pathlib import Path
from typing import Callable, Optional, Dict, Any

from autodub.models.project import Project
from autodub.jobs.job import Job


@dataclass
class PipelineContext:
    job: Job
    project: Project
    config: Any
    workspace: Path
    is_cancelled: Callable[[], bool] = lambda: False
    progress_callback: Optional[Callable[[Dict[str, Any]], None]] = None

    def emit_progress(self, stage: str, stage_percent: float, overall_percent: float, message: str = "") -> None:
        if self.progress_callback:
            event = {
                "event": "progress",
                "job_id": self.job.job_id,
                "project_id": self.job.project_id,
                "stage": stage,
                "stage_percent": round(stage_percent, 1),
                "overall_percent": round(overall_percent, 1),
                "status": self.job.status,
                "message": message,
            }
            self.progress_callback(event)
