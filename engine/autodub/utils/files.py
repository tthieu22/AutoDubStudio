import shutil
from pathlib import Path

def ensure_project_structure(project_dir: Path):
    dirs = [
        project_dir / "source",
        project_dir / "story",
        project_dir / "story" / "chapters",
        project_dir / "story" / "summaries",
        project_dir / "characters",
        project_dir / "scenes",
        project_dir / "assets",
        project_dir / "assets" / "images",
        project_dir / "assets" / "video",
        project_dir / "assets" / "music",
        project_dir / "audio",
        project_dir / "audio" / "tts",
        project_dir / "audio" / "bgm",
        project_dir / "audio" / "synced",
        project_dir / "transcript",
        project_dir / "timeline",
        project_dir / "subtitles",
        project_dir / "output",
        project_dir / "logs"
    ]
    for d in dirs:
        d.mkdir(parents=True, exist_ok=True)

def validate_project_format_v1(project_dir: Path) -> dict:
    """
    Validate project folder against AutoDubStudio Project Format Standard v1.
    Checks:
    - project.json existence and schema
    - directory layout (source, story, scenes, audio, subtitles, output, logs)
    - relative paths portability (no hardcoded absolute C:\\ or D:\\ drive paths)
    """
    p_dir = Path(project_dir)
    errors = []
    warnings = []

    p_json = p_dir / "project.json"
    if not p_json.exists():
        errors.append("Missing project.json in project root directory.")
        return {"valid": False, "errors": errors, "warnings": warnings, "portable": False}

    try:
        import json
        with open(p_json, "r", encoding="utf-8") as f:
            data = json.load(f)
        if "project_id" not in data or "name" not in data:
            errors.append("project.json missing required 'project_id' or 'name' fields.")
    except Exception as e:
        errors.append(f"Invalid project.json format: {e}")
        return {"valid": False, "errors": errors, "warnings": warnings, "portable": False}

    required_dirs = ["source", "story", "scenes", "audio", "subtitles", "output", "logs"]
    for rd in required_dirs:
        d_path = p_dir / rd
        if not d_path.exists():
            warnings.append(f"Standard directory '{rd}/' missing (will be created automatically).")

    json_str = json.dumps(data)
    if "C:\\" in json_str or "C:/" in json_str or "D:\\" in json_str or "D:/" in json_str:
        warnings.append("Hardcoded absolute system drive paths found in project.json. Use relative paths for 100% portability.")

    return {
        "valid": len(errors) == 0,
        "errors": errors,
        "warnings": warnings,
        "format_version": "v1.0",
        "portable": len(warnings) == 0 and len(errors) == 0
    }

def atomic_write_json(file_path: Path, data: dict, max_retries: int = 5):
    file_path = Path(file_path)
    file_path.parent.mkdir(parents=True, exist_ok=True)
    tmp_path = file_path.with_suffix(file_path.suffix + ".tmp")
    import json
    import os
    import time
    with open(tmp_path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    
    for attempt in range(max_retries):
        try:
            os.replace(tmp_path, file_path)
            return
        except OSError as e:
            if attempt == max_retries - 1:
                try:
                    with open(file_path, "w", encoding="utf-8") as f:
                        json.dump(data, f, indent=2, ensure_ascii=False)
                    if tmp_path.exists():
                        try: tmp_path.unlink()
                        except OSError: pass
                except Exception:
                    raise e
            else:
                time.sleep(0.05 * (attempt + 1))
