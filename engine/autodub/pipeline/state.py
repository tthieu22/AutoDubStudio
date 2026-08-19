from enum import Enum
from typing import List
from autodub.exceptions import StateTransitionError, StageDependencyError

class StageStatus(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    SKIPPED = "skipped"

class PipelineStage(str, Enum):
    EXTRACT = "extract"
    TRANSCRIBE = "transcribe"
    TRANSLATE = "translate"
    TTS = "tts"
    SYNC = "sync"
    RENDER = "render"

STAGE_ORDER: List[PipelineStage] = [
    PipelineStage.EXTRACT,
    PipelineStage.TRANSCRIBE,
    PipelineStage.TRANSLATE,
    PipelineStage.TTS,
    PipelineStage.SYNC,
    PipelineStage.RENDER,
]

VALID_TRANSITIONS = {
    StageStatus.PENDING: {StageStatus.RUNNING},
    StageStatus.RUNNING: {StageStatus.COMPLETED, StageStatus.FAILED, StageStatus.CANCELLED},
    StageStatus.FAILED: {StageStatus.RUNNING},
    StageStatus.CANCELLED: {StageStatus.RUNNING},
    StageStatus.SKIPPED: {StageStatus.RUNNING},
    StageStatus.COMPLETED: set(),  # Allowed only with force=True
}

def validate_state_transition(current_status: StageStatus, new_status: StageStatus, force: bool = False) -> None:
    if current_status == new_status:
        return
    if current_status == StageStatus.COMPLETED and new_status == StageStatus.RUNNING:
        if not force:
            raise StateTransitionError(f"Cannot transition COMPLETED stage to RUNNING without force option.")
        return
    allowed = VALID_TRANSITIONS.get(current_status, set())
    if new_status not in allowed and not force:
        raise StateTransitionError(f"Invalid state transition from '{current_status}' to '{new_status}'.")

def get_previous_stage(stage: PipelineStage) -> PipelineStage | None:
    idx = STAGE_ORDER.index(stage)
    if idx == 0:
        return None
    return STAGE_ORDER[idx - 1]
