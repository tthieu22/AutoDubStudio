from pathlib import Path
from typing import Dict, Any
from autodub.models.project import Project
from autodub.pipeline.state import STAGE_ORDER, PipelineStage, StageStatus, get_previous_stage
from autodub.exceptions import ProjectValidationError

class ProjectValidator:
    @staticmethod
    def validate(project: Project) -> bool:
        data = project.data
        if not data:
            raise ProjectValidationError("Project data is empty.")

        # 1. Version & Metadata
        if data.get("version") != 1:
            raise ProjectValidationError(f"Invalid or unsupported project version: {data.get('version')}")
        if not data.get("project_id"):
            raise ProjectValidationError("Missing project_id.")
        if not data.get("name"):
            raise ProjectValidationError("Missing project name.")

        # 2. Source & Target
        source = data.get("source", {})
        if not source.get("path"):
            raise ProjectValidationError("Missing source path.")
        target = data.get("target", {})
        if not target.get("language"):
            raise ProjectValidationError("Missing target language.")

        # 3. Settings
        settings = data.get("settings", {})
        required_settings = ["whisper_model", "whisper_compute_type", "translation_model", "tts_engine"]
        for key in required_settings:
            if key not in settings:
                raise ProjectValidationError(f"Missing required setting: {key}")

        # 4. Pipeline States & Dependencies
        pipeline = data.get("pipeline", {})
        for idx, stage in enumerate(STAGE_ORDER):
            stage_data = pipeline.get(stage.value)
            if not stage_data:
                raise ProjectValidationError(f"Missing pipeline stage entry: '{stage.value}'")
            
            status = stage_data.get("status")
            try:
                StageStatus(status)
            except ValueError:
                raise ProjectValidationError(f"Invalid status '{status}' for stage '{stage.value}'")

            # Dependency check
            prev_stage = get_previous_stage(stage)
            if prev_stage:
                prev_status = pipeline.get(prev_stage.value, {}).get("status")
                # If current stage is RUNNING or COMPLETED, previous stage MUST be COMPLETED
                if status in (StageStatus.RUNNING.value, StageStatus.COMPLETED.value):
                    if prev_status != StageStatus.COMPLETED.value:
                        raise ProjectValidationError(
                            f"Invalid stage dependency: Stage '{stage.value}' is {status}, but previous stage '{prev_stage.value}' is {prev_status}."
                        )

        return True
