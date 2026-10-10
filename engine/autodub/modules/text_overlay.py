from pathlib import Path
from typing import Dict, Any, Optional
from autodub.models.project import Project

class TextOverlayEngine:
    def __init__(self, project: Project):
        self.project = project

    def build_chapter_title_filter(self, episode_title: str, duration_sec: float = 3.0) -> str:
        """Returns an FFmpeg drawtext filter string for opening chapter title card."""
        safe_title = episode_title.replace(":", "\\:").replace("'", "'\\\\''")
        filter_str = (
            f"drawtext=text='{safe_title}':x=(w-text_w)/2:y=(h-text_h)/2-40:"
            f"fontsize=48:fontcolor=white:box=1:boxcolor=black@0.6:boxborderw=10:"
            f"enable='between(t,0,{duration_sec:.2f})'"
        )
        return filter_str
