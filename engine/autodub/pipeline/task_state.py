import datetime
from enum import Enum
from typing import Dict, Any, Optional, Set
from autodub.exceptions import StateTransitionError

class TaskStatus(str, Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    GENERATED = "generated"
    REVIEW_REQUIRED = "review_required"
    APPROVED = "approved"
    REJECTED = "rejected"
    FAILED = "failed"

VALID_TASK_TRANSITIONS: Dict[TaskStatus, Set[TaskStatus]] = {
    TaskStatus.PENDING: {TaskStatus.PROCESSING},
    TaskStatus.PROCESSING: {TaskStatus.GENERATED, TaskStatus.REVIEW_REQUIRED, TaskStatus.FAILED},
    TaskStatus.GENERATED: {TaskStatus.REVIEW_REQUIRED, TaskStatus.APPROVED},
    TaskStatus.REVIEW_REQUIRED: {TaskStatus.APPROVED, TaskStatus.REJECTED},
    TaskStatus.REJECTED: {TaskStatus.PROCESSING, TaskStatus.PENDING},
    TaskStatus.FAILED: {TaskStatus.PROCESSING, TaskStatus.PENDING},
    TaskStatus.APPROVED: set(),  # Allowed only with force=True
}

class TaskRecord:
    def __init__(
        self,
        task_id: str,
        project_id: str,
        stage: str,
        status: TaskStatus = TaskStatus.PENDING,
        attempt: int = 1,
        max_attempts: int = 3,
        artifact_path: Optional[str] = None,
        error: Optional[str] = None
    ):
        now = datetime.datetime.now(datetime.timezone.utc).isoformat()
        self.task_id = task_id
        self.project_id = project_id
        self.stage = stage
        self.status = status if isinstance(status, TaskStatus) else TaskStatus(str(status).lower())
        self.attempt = attempt
        self.max_attempts = max_attempts
        self.artifact_path = artifact_path
        self.error = error
        self.created_at = now
        self.updated_at = now

    def to_dict(self) -> Dict[str, Any]:
        return {
            "task_id": self.task_id,
            "project_id": self.project_id,
            "stage": self.stage,
            "status": self.status.value,
            "attempt": self.attempt,
            "max_attempts": self.max_attempts,
            "artifact_path": self.artifact_path,
            "error": self.error,
            "created_at": self.created_at,
            "updated_at": self.updated_at
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "TaskRecord":
        rec = cls(
            task_id=data["task_id"],
            project_id=data.get("project_id", "default"),
            stage=data.get("stage", "general"),
            status=TaskStatus(data.get("status", "pending")),
            attempt=data.get("attempt", 1),
            max_attempts=data.get("max_attempts", 3),
            artifact_path=data.get("artifact_path"),
            error=data.get("error")
        )
        if "created_at" in data:
            rec.created_at = data["created_at"]
        if "updated_at" in data:
            rec.updated_at = data["updated_at"]
        return rec

class TaskStateMachine:
    @staticmethod
    def transition(task: TaskRecord, new_status: TaskStatus, force: bool = False, error: Optional[str] = None) -> TaskRecord:
        curr_status = task.status
        if curr_status == new_status:
            return task

        if curr_status == TaskStatus.APPROVED and new_status != TaskStatus.APPROVED and not force:
            raise StateTransitionError(f"Task '{task.task_id}' is APPROVED. Cannot transition without force=True.")

        allowed = VALID_TASK_TRANSITIONS.get(curr_status, set())
        if new_status not in allowed and not force:
            raise StateTransitionError(f"Invalid Task transition from '{curr_status.value}' to '{new_status.value}'.")

        task.status = new_status
        task.updated_at = datetime.datetime.now(datetime.timezone.utc).isoformat()
        if error is not None:
            task.error = error
        elif new_status in (TaskStatus.PROCESSING, TaskStatus.APPROVED, TaskStatus.GENERATED):
            task.error = None

        return task

    @staticmethod
    def approve(task: TaskRecord) -> TaskRecord:
        return TaskStateMachine.transition(task, TaskStatus.APPROVED)

    @staticmethod
    def reject(task: TaskRecord, reason: Optional[str] = None) -> TaskRecord:
        return TaskStateMachine.transition(task, TaskStatus.REJECTED, error=reason or "Task rejected during review.")

    @staticmethod
    def fail(task: TaskRecord, error: str) -> TaskRecord:
        return TaskStateMachine.transition(task, TaskStatus.FAILED, error=error)

    @staticmethod
    def retry(task: TaskRecord) -> TaskRecord:
        if task.attempt >= task.max_attempts:
            raise StateTransitionError(f"Task '{task.task_id}' exceeded max attempts ({task.max_attempts}).")
        task.attempt += 1
        return TaskStateMachine.transition(task, TaskStatus.PROCESSING, force=True)
