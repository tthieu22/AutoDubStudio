import json
from pathlib import Path
from typing import Dict, Any, List
from autodub.models.project import Project
from autodub.pipeline.task_state import TaskStatus
from autodub.utils.logging import ProjectLogger

class StoryPipelineRecovery:
    def __init__(self, project: Project):
        self.project = project
        self.project_dir = project.project_dir
        self.logger = ProjectLogger(self.project_dir, project_id=project.data.get("project_id"))

    def scan_recovery_state(self) -> Dict[str, Any]:
        """Scans project directory artifacts to determine current resume point."""
        state = {
            "story_fetched": (self.project_dir / "story" / "original.txt").exists(),
            "story_cleaned": (self.project_dir / "story" / "cleaned.txt").exists(),
            "characters_analyzed": (self.project_dir / "characters" / "characters.json").exists(),
            "total_scenes": 0,
            "approved_images": 0,
            "approved_audio": 0,
            "timeline_built": (self.project_dir / "timeline" / "timeline.json").exists(),
            "preview_rendered": (self.project_dir / "preview" / "preview.mp4").exists(),
            "final_rendered": (self.project_dir / "output" / "final.mp4").exists(),
            "next_action": "FETCH_STORY"
        }

        scene_files = list((self.project_dir / "scenes").glob("scene_*.json"))
        state["total_scenes"] = len(scene_files)

        for sf in scene_files:
            try:
                with open(sf, "r", encoding="utf-8") as f:
                    sc = json.load(f)
                    if sc.get("image_path") and (self.project_dir / sc["image_path"]).exists():
                        state["approved_images"] += 1
                    if sc.get("audio_path") and (self.project_dir / sc["audio_path"]).exists():
                        state["approved_audio"] += 1
            except Exception:
                pass

        if not state["story_fetched"]:
            state["next_action"] = "FETCH_STORY"
        elif not state["story_cleaned"]:
            state["next_action"] = "CLEAN_STORY"
        elif not state["characters_analyzed"]:
            state["next_action"] = "ANALYZE_STORY"
        elif state["total_scenes"] == 0:
            state["next_action"] = "PLAN_SCENES"
        elif state["approved_images"] < state["total_scenes"]:
            state["next_action"] = "GENERATE_IMAGES"
        elif state["approved_audio"] < state["total_scenes"]:
            state["next_action"] = "GENERATE_AUDIO"
        elif not state["timeline_built"]:
            state["next_action"] = "BUILD_TIMELINE"
        elif not state["final_rendered"]:
            state["next_action"] = "RENDER_FINAL"
        else:
            state["next_action"] = "COMPLETED"

        self.logger.info("pipeline", f"Recovery scan complete. Next action: {state['next_action']}")
        return state
