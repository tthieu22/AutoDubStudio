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

def validate_state_transition(current_status: StageStatus | str, new_status: StageStatus | str, force: bool = False) -> None:
    raw_curr = current_status.value if hasattr(current_status, "value") else str(current_status)
    raw_new = new_status.value if hasattr(new_status, "value") else str(new_status)
    try:
        curr_enum = StageStatus(raw_curr.lower())
    except ValueError:
        curr_enum = StageStatus.PENDING

    try:
        new_enum = StageStatus(raw_new.lower())
    except ValueError:
        new_enum = StageStatus.RUNNING

    if curr_enum == new_enum:
        return
    if curr_enum == StageStatus.COMPLETED and new_enum == StageStatus.RUNNING:
        if not force:
            raise StateTransitionError(f"Cannot transition COMPLETED stage to RUNNING without force option.")
        return
    allowed = VALID_TRANSITIONS.get(curr_enum, set())
    if new_enum not in allowed and not force:
        raise StateTransitionError(f"Invalid state transition from '{curr_enum}' to '{new_enum}'.")

def get_previous_stage(stage: PipelineStage) -> PipelineStage | None:
    idx = STAGE_ORDER.index(stage)
    if idx == 0:
        return None
    return STAGE_ORDER[idx - 1]
