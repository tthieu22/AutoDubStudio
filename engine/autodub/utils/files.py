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
