import json
from pathlib import Path
from typing import Dict, Any, List, Optional
from autodub.models.project import Project

class TimelineEngine:
    def __init__(self, project: Project):
        self.project = project
        self.project_dir = project.project_dir
        self.timeline_dir = self.project_dir / "timeline"
        self.timeline_dir.mkdir(parents=True, exist_ok=True)

    def build_timeline(self, scenes: List[Dict[str, Any]]) -> Dict[str, Any]:
        video_track = []
        audio_voice_track = []
        dialogue_track = []
        subtitle_track = []

        current_time = 0.0

        for sc in scenes:
            scene_id = sc.get("id", "scene_001")
            dur = float(sc.get("duration") or sc.get("audio_duration") or 5.0)
            start_t = current_time
            end_t = current_time + dur
            current_time = end_t

            speaker = sc.get("speaker", "NARRATOR")
            narration = sc.get("narration", "")
            img_path = sc.get("image_path") or f"assets/images/{scene_id}.png"
            wav_path = sc.get("audio_path") or f"assets/audio/{scene_id}.wav"

            # Video track item
            video_track.append({
                "id": f"v_{scene_id}",
                "scene_id": scene_id,
                "start": start_t,
                "end": end_t,
                "duration": dur,
                "asset_path": img_path
            })

            # Voice / Dialogue track item
            audio_item = {
                "id": f"a_{scene_id}",
                "scene_id": scene_id,
                "speaker": speaker,
                "start": start_t,
                "end": end_t,
                "duration": dur,
                "asset_path": wav_path,
                "volume": 1.0
            }
            if speaker == "NARRATOR":
                audio_voice_track.append(audio_item)
            else:
                dialogue_track.append(audio_item)

            # Subtitle track item
            subtitle_track.append({
                "id": f"sub_{scene_id}",
                "speaker": speaker,
                "start": start_t,
                "end": end_t,
                "text": narration
            })

        timeline_data = {
            "version": 1,
            "project_id": self.project.data.get("project_id", "default"),
            "total_duration": round(current_time, 2),
            "tracks": [
                {"name": "Video Track", "type": "video", "items": video_track},
                {"name": "Narration Track", "type": "audio", "items": audio_voice_track},
                {"name": "Dialogue Track", "type": "dialogue", "items": dialogue_track},
                {"name": "Background Music Track", "type": "music", "items": []},
                {"name": "SFX Track", "type": "sfx", "items": []},
                {"name": "Subtitle Track", "type": "subtitle", "items": subtitle_track}
            ]
        }

        # Save timeline.json
        timeline_file = self.timeline_dir / "timeline.json"
        with open(timeline_file, "w", encoding="utf-8") as f:
            json.dump(timeline_data, f, indent=2, ensure_ascii=False)

        self.project.data["timeline"] = timeline_data
        self.project.save()

        return timeline_data
