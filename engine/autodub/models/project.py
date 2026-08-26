import json
import os
import uuid
import datetime
from pathlib import Path
from typing import Dict, Any, Optional
from autodub.pipeline.state import STAGE_ORDER, StageStatus
from autodub.exceptions import ProjectValidationError

class Project:
    def __init__(self, project_dir: Path, name: Optional[str] = None, source_path: Optional[str] = None, mode: str = "MODE_DUBBING"):
        self.project_dir = Path(project_dir)
        self.project_file = self.project_dir / "project.json"
        self.tmp_file = self.project_dir / "project.json.tmp"
        self.bak_file = self.project_dir / "project.json.bak"
        self.data: Dict[str, Any] = {}

        if self.project_file.exists():
            self.load()
        elif self.bak_file.exists():
            self.recover_from_backup()
        else:
            self._init_defaults(name or self.project_dir.name, source_path, mode=mode)
            self.save()

    def _init_defaults(self, name: str, source_path: Optional[str] = None, mode: str = "MODE_DUBBING"):
        now = datetime.datetime.now(datetime.timezone.utc).isoformat()
        rel_source = source_path if source_path else ("source/input.mp4" if mode == "MODE_DUBBING" else "source/story_source.json")
        
        version_num = 1 if mode == "MODE_DUBBING" else 2
        self.data = {
            "version": version_num,
            "project_id": str(uuid.uuid4()),
            "name": name,
            "mode": mode,  # "MODE_DUBBING" or "MODE_STORY"
            "created_at": now,
            "updated_at": now,
            "source": {
                "path": rel_source,
                "language": "en"
            },
            "target": {
                "language": "vi"
            },
            "settings": {
                "whisper_model": "small",
                "whisper_compute_type": "int8",
                "translation_model": "qwen2.5-3b-instruct",
                "translation_batch_size": 3,
                "tts_engine": "piper",
                "chunk_duration": 600,
                "image_model": "sd1.5-lcm"
            },
            "pipeline": {
                stage.value: {
                    "status": StageStatus.PENDING.value,
                    "progress": 0,
                    "current": 0,
                    "total": 0,
                    "error": None
                } for stage in STAGE_ORDER
            },
            "segments": [],
            "story": {
                "source_type": None,
                "source_url": None,
                "title": None,
                "author": None,
                "license": None,
                "status": "PENDING"
            },
            "characters": [],
            "scenes": [],
            "timeline": {
                "duration": 0.0,
                "tracks": []
            },
            "metadata": {}
        }

    def load(self):
        try:
            with open(self.project_file, "r", encoding="utf-8") as f:
                self.data = json.load(f)
            # Ensure required default sections exist
            modified = False
            if "mode" not in self.data:
                self.data["mode"] = "MODE_DUBBING"
                modified = True
            if "pipeline" not in self.data:
                self.data["pipeline"] = {
                    stage.value: {
                        "status": StageStatus.PENDING.value,
                        "progress": 0,
                        "current": 0,
                        "total": 0,
                        "error": None
                    } for stage in STAGE_ORDER
                }
                modified = True
            if "segments" not in self.data:
                self.data["segments"] = []
                modified = True
            if "story" not in self.data:
                self.data["story"] = {"source_type": None, "title": None, "status": "PENDING"}
                modified = True
            if "characters" not in self.data:
                self.data["characters"] = []
                modified = True
            if "scenes" not in self.data:
                self.data["scenes"] = []
                modified = True
            if "timeline" not in self.data:
                self.data["timeline"] = {"duration": 0.0, "tracks": []}
                modified = True
            if "metadata" not in self.data:
                self.data["metadata"] = {}
                modified = True
            if modified:
                self.save()
        except (json.JSONDecodeError, OSError) as e:
            if self.bak_file.exists():
                self.recover_from_backup()
            else:
                raise ProjectValidationError(f"Failed to load project file '{self.project_file}': {e}")

    def recover_from_backup(self):
        if not self.bak_file.exists():
            raise ProjectValidationError(f"Backup file '{self.bak_file}' does not exist for recovery.")
        with open(self.bak_file, "r", encoding="utf-8") as f:
            self.data = json.load(f)
        # Restore main project file atomically
        self.save()

    def save(self):
        self.project_dir.mkdir(parents=True, exist_ok=True)
        self.data["updated_at"] = datetime.datetime.now(datetime.timezone.utc).isoformat()

        # If current project.json exists and is valid JSON, update project.json.bak
        if self.project_file.exists():
            try:
                with open(self.project_file, "r", encoding="utf-8") as f:
                    json.load(f)  # Ensure it's not corrupt before backing up
                with open(self.bak_file, "w", encoding="utf-8") as f_bak:
                    json.dump(self.data, f_bak, indent=2, ensure_ascii=False)
            except Exception:
                pass

        # Write data to tmp_file
        with open(self.tmp_file, "w", encoding="utf-8") as f_tmp:
            json.dump(self.data, f_tmp, indent=2, ensure_ascii=False)
            f_tmp.flush()
            os.fsync(f_tmp.fileno())

        # Atomic replace project.json.tmp -> project.json
        os.replace(self.tmp_file, self.project_file)

        # Ensure backup exists even on first save
        if not self.bak_file.exists():
            with open(self.bak_file, "w", encoding="utf-8") as f_bak:
                json.dump(self.data, f_bak, indent=2, ensure_ascii=False)

    def get_stage_info(self, stage_name: str) -> Dict[str, Any]:
        return self.data.get("pipeline", {}).get(stage_name.lower(), {
            "status": StageStatus.PENDING.value,
            "progress": 0,
            "current": 0,
            "total": 0,
            "error": None
        })

    def update_stage(
        self,
        stage_name: str,
        status: str,
        progress: Optional[int] = None,
        current: Optional[int] = None,
        total: Optional[int] = None,
        error: Optional[str] = None
    ):
        stage_key = stage_name.lower()
        if "pipeline" not in self.data:
            self.data["pipeline"] = {}
        if stage_key not in self.data["pipeline"]:
            self.data["pipeline"][stage_key] = {}

        st = self.data["pipeline"][stage_key]
        st["status"] = status
        if progress is not None:
            st["progress"] = progress
        if current is not None:
            st["current"] = current
        if total is not None:
            st["total"] = total
        if error is not None:
            st["error"] = error
        elif status == StageStatus.RUNNING.value or status == StageStatus.COMPLETED.value:
            st["error"] = None

        self.save()
