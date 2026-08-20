from enum import Enum
from typing import Dict, Set
from autodub.exceptions import InvalidJobStateTransitionError


class JobState(Enum):
    PENDING = "PENDING"
    QUEUED = "QUEUED"
    RUNNING = "RUNNING"
    PAUSED = "PAUSED"
    CANCEL_REQUESTED = "CANCEL_REQUESTED"
    CANCELLED = "CANCELLED"
    RETRYING = "RETRYING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    RECOVERING = "RECOVERING"


ALLOWED_TRANSITIONS: Dict[JobState, Set[JobState]] = {
    JobState.PENDING: {JobState.QUEUED, JobState.CANCELLED, JobState.FAILED},
    JobState.QUEUED: {JobState.RUNNING, JobState.CANCELLED, JobState.PAUSED},
    JobState.RUNNING: {
        JobState.COMPLETED,
        JobState.FAILED,
        JobState.PAUSED,
        JobState.CANCEL_REQUESTED,
        JobState.CANCELLED,
        JobState.RECOVERING,
    },
    JobState.PAUSED: {JobState.QUEUED, JobState.CANCELLED},
    JobState.CANCEL_REQUESTED: {JobState.CANCELLED, JobState.FAILED},
    JobState.CANCELLED: {JobState.QUEUED, JobState.PENDING},  # Allowed to re-queue / retry
    JobState.RETRYING: {JobState.QUEUED, JobState.FAILED, JobState.CANCELLED},
    JobState.RECOVERING: {JobState.QUEUED, JobState.RUNNING, JobState.FAILED, JobState.CANCELLED},
    JobState.COMPLETED: {JobState.QUEUED},  # Allowed to force re-run
    JobState.FAILED: {JobState.RETRYING, JobState.QUEUED, JobState.PENDING},
}


def validate_job_state_transition(current_state: str, new_state: str, force: bool = False) -> None:
    """Validate transition from current_state to new_state."""
    if force:
        return

    try:
        curr_enum = JobState(current_state.upper())
        new_enum = JobState(new_state.upper())
    except ValueError as e:
        raise InvalidJobStateTransitionError(f"Invalid job state string: {e}")

    if curr_enum == new_enum:
        return

    allowed = ALLOWED_TRANSITIONS.get(curr_enum, set())
    if new_enum not in allowed:
        raise InvalidJobStateTransitionError(
            f"Invalid job state transition from '{curr_enum.value}' to '{new_enum.value}'."
        )


def is_terminal_job_state(state: str) -> bool:
    """Check if state is terminal (COMPLETED, CANCELLED)."""
    return state.upper() in {JobState.COMPLETED.value, JobState.CANCELLED.value}
