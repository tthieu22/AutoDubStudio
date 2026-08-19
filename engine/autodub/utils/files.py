import shutil
from pathlib import Path

def ensure_project_structure(project_dir: Path):
    dirs = [
        project_dir / "source",
        project_dir / "audio",
        project_dir / "transcript",
        project_dir / "tts",
        project_dir / "preview",
        project_dir / "output",
        project_dir / "logs"
    ]
    for d in dirs:
        d.mkdir(parents=True, exist_ok=True)

def atomic_write_json(file_path: Path, data: dict):
    file_path = Path(file_path)
    file_path.parent.mkdir(parents=True, exist_ok=True)
    tmp_path = file_path.with_suffix(file_path.suffix + ".tmp")
    import json
    import os
    with open(tmp_path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    os.replace(tmp_path, file_path)
