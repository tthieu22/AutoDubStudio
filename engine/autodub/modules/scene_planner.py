import json
import requests
from pathlib import Path
from typing import Dict, Any, List, Optional
from autodub.models.project import Project
from autodub.pipeline.task_state import TaskStatus, TaskRecord, TaskStateMachine
from autodub.modules.story_memory import StoryMemoryEngine
from autodub.modules.llamacpp_client import strip_think_tags

OLLAMA_GENERATE_URL = "http://localhost:11434/api/generate"

class ScenePlanner:
    def __init__(self, model_name: str = "qwen2.5-3b-instruct", ollama_url: str = OLLAMA_GENERATE_URL):
        self.model_name = model_name
        self.ollama_url = ollama_url

    def _call_qwen_json(self, prompt: str) -> List[Dict[str, Any]]:
        payload = {
            "model": self.model_name,
            "prompt": prompt,
            "stream": False,
            "format": "json"
        }
        try:
            res = requests.post(self.ollama_url, json=payload, timeout=30)
            if res.status_code == 200:
                raw_text = res.json().get("response", "[]")
                from autodub.modules.structured_parser import StructuredParser
                parsed = StructuredParser.extract_json_payload(raw_text)
                if isinstance(parsed, list):
                    return parsed
                elif isinstance(parsed, dict) and "scenes" in parsed:
                    return parsed["scenes"]
        except Exception:
            pass
        return []

    def plan_chapter_scenes(self, project: Project, chapter_index: int) -> List[Dict[str, Any]]:
        project_dir = project.project_dir
        chap_file = project_dir / "story" / "chapters" / f"chapter_{chapter_index:03d}.txt"
        if not chap_file.exists():
            raise FileNotFoundError(f"Chapter file not found: {chap_file}")

        chap_text = chap_file.read_text(encoding="utf-8")
        memory = StoryMemoryEngine(project)
        context_prompt = memory.build_context_prompt(chapter_index, chap_text)

        prompt = f"""
{context_prompt}

=== YÊU CẦU PHÂN TÁCH PHÂN CẢNH (SCENE PLANNER) ===
Hãy chia nội dung chương trên thành danh sách các Scene video ngắn (10-30s mỗi scene).

CẤU TRÚC JSON MẪU:
[
  {{
    "scene_index": 1,
    "speaker": "NARRATOR",
    "narration": "Đêm đó, mưa giăng kín ngôi làng cổ lặng lẽ.",
    "visual_prompt": "ancient chinese village at dark rainy night, cinematic lighting, 8k wallpaper",
    "duration": 8
  }},
  {{
    "scene_index": 2,
    "speaker": "A_LANG",
    "narration": "Ai đang đứng ở ngoài cổng làng đó?",
    "visual_prompt": "mysterious young man holding a red lantern walking near a wooden village gate in rain",
    "duration": 6
  }}
]

[OUTPUT CONTRACT - STRICT RAW JSON ONLY]
- Trả về DUY NHẤT 1 Mảng JSON (JSON Array) hợp lệ.
- CẤM kèm bất kỳ lời dẫn, giải thích hay khối markdown codeblock (```json ... ```).
- ĐẦU RA BẮT ĐẦU BẰNG KÝ TỰ '[' VÀ KẾT THÚC BẰNG ']'.
"""
        raw_scenes = self._call_qwen_json(prompt)

        # Fallback if LLM output failed to parse or empty
        if not raw_scenes:
            lines = [l.strip() for l in chap_text.splitlines() if l.strip()][:3]
            raw_scenes = [
                {
                    "scene_index": idx,
                    "speaker": "NARRATOR",
                    "narration": line,
                    "visual_prompt": f"cinematic scene representing {line[:30]}, detailed illustration",
                    "duration": 8
                }
                for idx, line in enumerate(lines, start=1)
            ]

        scenes_dir = project_dir / "scenes"
        scenes_dir.mkdir(parents=True, exist_ok=True)

        final_scenes = []
        global_scene_counter = len(list(scenes_dir.glob("scene_*.json")))

        for item in raw_scenes:
            global_scene_counter += 1
            scene_data = {
                "id": f"scene_{global_scene_counter:03d}",
                "chapter_index": chapter_index,
                "scene_index": item.get("scene_index", global_scene_counter),
                "speaker": item.get("speaker", "NARRATOR"),
                "narration": item.get("narration", ""),
                "visual_prompt": item.get("visual_prompt", ""),
                "duration": item.get("duration", 8),
                "status": TaskStatus.REVIEW_REQUIRED.value, # Mandatory Review Gate 3
                "image_path": None,
                "audio_path": None
            }

            # Save individual scene file
            scene_file = scenes_dir / f"{scene_data['id']}.json"
            with open(scene_file, "w", encoding="utf-8") as f:
                json.dump(scene_data, f, indent=2, ensure_ascii=False)

            final_scenes.append(scene_data)

        # Update Project Data
        existing_scenes = project.data.get("scenes", [])
        existing_scenes.extend(final_scenes)
        project.data["scenes"] = existing_scenes
        project.save()

        return final_scenes
