import json
from pathlib import Path
from typing import Dict, Any, List
from autodub.models.project import Project
from autodub.modules.transcriber import format_srt_timestamp

def format_ass_timestamp(seconds: float) -> str:
    """Format seconds float into ASS timestamp H:MM:SS.cs"""
    h = int(seconds // 3600)
    m = int((seconds % 3600) // 60)
    s = int(seconds % 60)
    cs = int(round((seconds - int(seconds)) * 100))
    if cs >= 100:
        s += 1
        cs = 0
    return f"{h}:{m:02d}:{s:02d}.{cs:02d}"

class SubtitleEngine:
    ASS_HEADER = """[Script Info]
Title: AutoDubStudio Story Subtitles
ScriptType: v4.00+
WrapStyle: 0
ScaledBorderAndShadow: yes
YCbCr Matrix: None
PlayResX: 1920
PlayResY: 1080

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Narrator,Arial,48,&H00FFFFFF,&H000000FF,&H00000000,&H80000000,-1,0,0,0,100,100,0,0,1,2,2,2,40,40,40,1
Style: Character,Arial,52,&H0000FFFF,&H000000FF,&H00000000,&H80000000,-1,0,0,0,100,100,0,0,1,2,2,2,40,40,40,1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
"""

    def __init__(self, project: Project):
        self.project = project
        self.project_dir = project.project_dir
        self.subtitles_dir = self.project_dir / "subtitles"
        self.subtitles_dir.mkdir(parents=True, exist_ok=True)

    def generate_subtitles(self, scenes: List[Dict[str, Any]]) -> Dict[str, Path]:
        srt_lines = []
        ass_events = []
        current_time = 0.0

        for idx, sc in enumerate(scenes, start=1):
            dur = float(sc.get("duration") or sc.get("audio_duration") or 5.0)
            start_t = current_time
            end_t = current_time + dur
            current_time = end_t

            text = sc.get("narration", "").strip()
            speaker = sc.get("speaker", "NARRATOR")

            # 1. Build SRT
            srt_lines.append(str(idx))
            srt_lines.append(f"{format_srt_timestamp(start_t)} --> {format_srt_timestamp(end_t)}")
            srt_lines.append(f"[{speaker}] {text}" if speaker != "NARRATOR" else text)
            srt_lines.append("")

            # 2. Build ASS
            ass_style = "Narrator" if speaker == "NARRATOR" else "Character"
            start_ass = format_ass_timestamp(start_t)
            end_ass = format_ass_timestamp(end_t)
            ass_text = f"{speaker}: {text}" if speaker != "NARRATOR" else text
            ass_events.append(f"Dialogue: 0,{start_ass},{end_ass},{ass_style},{speaker},0,0,0,,{ass_text}")

        # Write SRT
        srt_file = self.subtitles_dir / "vi.srt"
        with open(srt_file, "w", encoding="utf-8") as f:
            f.write("\n".join(srt_lines).strip() + "\n")

        # Write ASS
        ass_file = self.subtitles_dir / "vi.ass"
        ass_content = self.ASS_HEADER + "\n".join(ass_events) + "\n"
        with open(ass_file, "w", encoding="utf-8") as f:
            f.write(ass_content)

        return {"srt": srt_file, "ass": ass_file}
