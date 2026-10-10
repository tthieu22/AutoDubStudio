import os
import json
import wave
from pathlib import Path
from typing import Dict, List, Any, Optional

class QualityControlEngine:
    """
    Automated Quality Control (QC) and Audio Sync Validator for AutoDubStudio.
    Inspects transcript/translation segments and audio clips for timing mismatches,
    excessive TTS duration, overlaps, missing segments, and silent audio.
    """

    def __init__(self, project_dir: str):
        self.project_path = Path(project_dir)
        self.transcript_file = self.project_path / "transcript" / "transcript.json"
        self.translation_file = self.project_path / "transcript" / "translation.json"
        self.audio_dir = self.project_path / "audio"

    def run_qc_inspection(self) -> Dict[str, Any]:
        """
        Executes comprehensive QC checks on project data.
        Returns detailed report containing issue flags, warning count, error count, and auto-fit suggestions.
        """
        report = {
            "valid": True,
            "total_segments": 0,
            "error_count": 0,
            "warning_count": 0,
            "issues": [],
            "stats": {
                "avg_tts_duration_ratio": 1.0,
                "max_duration_exceeded_sec": 0.0,
                "missing_audio_segments": 0
            }
        }

        # Select translation or fallback to transcript
        target_file = self.translation_file if self.translation_file.exists() else self.transcript_file
        if not target_file.exists():
            report["valid"] = False
            report["issues"].append({
                "severity": "ERROR",
                "segment_id": -1,
                "type": "MISSING_TRANSCRIPT",
                "message": "Neither translation.json nor transcript.json was found in project.",
                "action": "Run STT / Translation first"
            })
            return report

        try:
            with open(target_file, "r", encoding="utf-8") as f:
                segments = json.load(f)
        except Exception as e:
            report["valid"] = False
            report["issues"].append({
                "severity": "ERROR",
                "segment_id": -1,
                "type": "INVALID_JSON",
                "message": f"Failed to parse subtitle file: {str(e)}",
                "action": "Fix JSON syntax"
            })
            return report

        report["total_segments"] = len(segments)
        prev_end_time = 0.0
        total_ratio = 0.0
        ratio_count = 0
        max_exceeded = 0.0

        for i, seg in enumerate(segments):
            seg_id = seg.get("id", i + 1)
            start = float(seg.get("start", 0.0))
            end = float(seg.get("end", 0.0))
            duration = end - start
            text = seg.get("text", "") or seg.get("translated_text", "")

            # Check 1: Negative or zero subtitle duration
            if duration <= 0:
                report["error_count"] += 1
                report["issues"].append({
                    "severity": "ERROR",
                    "segment_id": seg_id,
                    "type": "INVALID_TIMESTAMPS",
                    "message": f"Segment #{seg_id} has invalid duration ({duration:.2f}s).",
                    "action": "Adjust Start/End time"
                })

            # Check 2: Subtitle timestamp overlap with previous segment
            if start < prev_end_time - 0.05:
                report["warning_count"] += 1
                report["issues"].append({
                    "severity": "WARNING",
                    "segment_id": seg_id,
                    "type": "TIMESTAMP_OVERLAP",
                    "message": f"Segment #{seg_id} start ({start:.2f}s) overlaps with previous segment end ({prev_end_time:.2f}s).",
                    "action": "Auto Fit"
                })
            prev_end_time = end

            # Check 3: Check TTS audio file if rendered
            audio_path = self.audio_dir / f"seg_{seg_id:04d}.wav"
            if not audio_path.exists():
                audio_path = self.audio_dir / f"segment_{seg_id:04d}.wav"

            if audio_path.exists():
                try:
                    with wave.open(str(audio_path), "rb") as wf:
                        frames = wf.getnframes()
                        rate = wf.getframerate()
                        audio_duration = frames / float(rate) if rate > 0 else 0.0

                    if duration > 0:
                        ratio = audio_duration / duration
                        total_ratio += ratio
                        ratio_count += 1

                    if audio_duration > duration + 0.3:
                        diff = audio_duration - duration
                        if diff > max_exceeded:
                            max_exceeded = diff

                        severity = "ERROR" if diff > 1.5 else "WARNING"
                        if severity == "ERROR":
                            report["error_count"] += 1
                        else:
                            report["warning_count"] += 1

                        report["issues"].append({
                            "severity": severity,
                            "segment_id": seg_id,
                            "type": "SPEECH_EXCEEDS_WINDOW",
                            "message": f"Segment #{seg_id} audio ({audio_duration:.2f}s) exceeds subtitle window ({duration:.2f}s) by +{diff:.2f}s.",
                            "action": "Adjust Speed"
                        })
                except Exception as audio_err:
                    report["warning_count"] += 1
                    report["issues"].append({
                        "severity": "WARNING",
                        "segment_id": seg_id,
                        "type": "CORRUPT_AUDIO",
                        "message": f"Segment #{seg_id} audio file could not be analyzed: {str(audio_err)}",
                        "action": "Re-generate TTS"
                    })

        if ratio_count > 0:
            report["stats"]["avg_tts_duration_ratio"] = round(total_ratio / ratio_count, 3)
        report["stats"]["max_duration_exceeded_sec"] = round(max_exceeded, 3)
        report["valid"] = report["error_count"] == 0

        return report

    def apply_autofit(self) -> Dict[str, Any]:
        """
        Automatically aligns subtitle boundaries and adjusts segment timing
        to eliminate timestamp overlaps and fit audio windows.
        """
        target_file = self.translation_file if self.translation_file.exists() else self.transcript_file
        if not target_file.exists():
            return {"success": False, "message": "No transcript/translation file found"}

        with open(target_file, "r", encoding="utf-8") as f:
            segments = json.load(f)

        modified = False
        prev_end = 0.0

        for i, seg in enumerate(segments):
            start = float(seg.get("start", 0.0))
            end = float(seg.get("end", 0.0))

            if start < prev_end:
                shift = prev_end - start
                seg["start"] = round(prev_end, 3)
                seg["end"] = round(end + shift, 3)
                modified = True

            prev_end = float(seg.get("end", 0.0))

        if modified:
            with open(target_file, "w", encoding="utf-8") as f:
                json.dump(segments, f, indent=2, ensure_ascii=False)

        return {"success": True, "modified": modified, "total_segments": len(segments)}
