import time
from typing import Callable, Optional
from autodub.models.project import Project
from autodub.pipeline.state import PipelineStage, StageStatus
from autodub.pipeline.progress import emit_event
from autodub.exceptions import PipelineCancelledError

class MockBaseStage:
    def __init__(self, stage: PipelineStage, steps: int = 10, step_delay: float = 0.1):
        self.stage = stage
        self.steps = steps
        self.step_delay = step_delay

    def run(self, project: Project, is_cancelled: Optional[Callable[[], bool]] = None, fail_at_step: Optional[int] = None):
        stage_name = self.stage.value
        stage_info = project.get_stage_info(stage_name)
        
        # Partial resume check: current step saved in project
        start_step = stage_info.get("current", 0)
        total_steps = self.steps

        if start_step >= total_steps:
            start_step = 0

        project.update_stage(stage_name, StageStatus.RUNNING.value, current=start_step, total=total_steps)
        emit_event("stage_start", stage_name, current=start_step, total=total_steps)

        for step in range(start_step + 1, total_steps + 1):
            if is_cancelled and is_cancelled():
                project.update_stage(stage_name, StageStatus.CANCELLED.value, current=step-1, total=total_steps)
                emit_event("stage_cancelled", stage_name, current=step-1, total=total_steps)
                raise PipelineCancelledError(f"Stage {stage_name} was cancelled by user.")

            if fail_at_step is not None and step == fail_at_step:
                err_msg = f"Simulated error in stage {stage_name} at step {step}"
                project.update_stage(stage_name, StageStatus.FAILED.value, current=step-1, total=total_steps, error=err_msg)
                emit_event("stage_error", stage_name, current=step-1, total=total_steps, error=err_msg)
                raise RuntimeError(err_msg)

            time.sleep(self.step_delay)
            percent = (step / total_steps) * 100
            project.update_stage(stage_name, StageStatus.RUNNING.value, progress=int(percent), current=step, total=total_steps)
            emit_event("progress", stage_name, current=step, total=total_steps, percent=percent)

        project.update_stage(stage_name, StageStatus.COMPLETED.value, progress=100, current=total_steps, total=total_steps)
        emit_event("stage_complete", stage_name, current=total_steps, total=total_steps)

class MockExtractor(MockBaseStage):
    def __init__(self, steps: int = 5, step_delay: float = 0.05):
        super().__init__(PipelineStage.EXTRACT, steps=steps, step_delay=step_delay)

class MockTranscriber(MockBaseStage):
    def __init__(self, steps: int = 10, step_delay: float = 0.05):
        super().__init__(PipelineStage.TRANSCRIBE, steps=steps, step_delay=step_delay)

class MockTranslator(MockBaseStage):
    def __init__(self, steps: int = 10, step_delay: float = 0.05):
        super().__init__(PipelineStage.TRANSLATE, steps=steps, step_delay=step_delay)

class MockTTS(MockBaseStage):
    def __init__(self, steps: int = 10, step_delay: float = 0.05):
        super().__init__(PipelineStage.TTS, steps=steps, step_delay=step_delay)

class MockSynchronizer(MockBaseStage):
    def __init__(self, steps: int = 5, step_delay: float = 0.05):
        super().__init__(PipelineStage.SYNC, steps=steps, step_delay=step_delay)

class MockRenderer(MockBaseStage):
    def __init__(self, steps: int = 5, step_delay: float = 0.05):
        super().__init__(PipelineStage.RENDER, steps=steps, step_delay=step_delay)
