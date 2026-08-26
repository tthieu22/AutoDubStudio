import json
import re
import requests
from pathlib import Path
from typing import Dict, Any, List, Optional
from autodub.models.project import Project
from autodub.modules.llamacpp_client import strip_think_tags

OLLAMA_GENERATE_URL = "http://localhost:11434/api/generate"

class StoryAnalyzer:
    def __init__(self, model_name: str = "qwen2.5-3b-instruct", ollama_url: str = OLLAMA_GENERATE_URL):
        self.model_name = model_name
        self.ollama_url = ollama_url

    def _call_qwen(self, prompt: str) -> str:
        payload = {
            "model": self.model_name,
            "prompt": prompt,
            "stream": False,
            "format": "json"
        }
        try:
            res = requests.post(self.ollama_url, json=payload, timeout=30)
            if res.status_code == 200:
                raw_res = res.json().get("response", "{}")
                return strip_think_tags(raw_res)
        except Exception:
            pass
        # Mock/Fallback if LLM call fails or during unit tests
        return "{}"

    def split_chapters(self, text: str) -> List[Dict[str, str]]:
        # Match Chapter/Chương headers or split by ~3000 chars paragraphs
        pattern = r"(?:^|\n)(Chapter\s+\d+|Chương\s+\d+|Hồi\s+\d+).*?(?=\n(?:Chapter\s+\d+|Chương\s+\d+|Hồi\s+\d+)|$)"
        matches = re.findall(pattern, text, flags=re.IGNORECASE | re.DOTALL)
        
        chapters = []
        splits = [s.strip() for s in re.split(r"(?:^|\n)(?=Chapter\s+\d+|Chương\s+\d+|Hồi\s+\d+)", text, flags=re.IGNORECASE) if s.strip()]
        if splits:
            for idx, part in enumerate(splits, start=1):
                lines = part.splitlines()
                title = lines[0] if lines else f"Chương {idx}"
                chapters.append({"chapter_index": idx, "title": title, "content": part})
        else:
            # Fallback split into ~3000 character chunks
            chunk_size = 3000
            for i in range(0, len(text), chunk_size):
                chunk = text[i:i + chunk_size].strip()
                if chunk:
                    idx = (i // chunk_size) + 1
                    chapters.append({"chapter_index": idx, "title": f"Chương {idx}", "content": chunk})

        return chapters

    def extract_entities_and_world(self, text_sample: str) -> Dict[str, Any]:
        prompt = f"""
Bạn là chuyên gia phân tích kịch bản. Hãy phân tích văn bản câu chuyện sau và trích xuất thông tin:
1. Danh sách nhân vật (characters): tên, giới tính (male/female), tính cách, tone giọng đọc đề xuất (piper voice model).
2. Bối cảnh thế giới (world): các địa danh chính, thời kỳ/bối cảnh.

Văn bản:
{text_sample[:2500]}

Trả về JSON với cấu trúc exact:
{{
  "characters": [
    {{
      "name": "Tên nhân vật",
      "gender": "male hoặc female",
      "tone": "trầm buồn / mạnh mẽ / vui vẻ",
      "assigned_voice": "vi_VN-viss-low.onnx"
    }}
  ],
  "world": {{
    "locations": ["Ngôi làng cổ", "Rừng trúc"],
    "era": "Thời cổ đại"
  }}
}}
"""
        response_text = self._call_qwen(prompt)
        try:
            parsed = json.loads(response_text)
            if "characters" in parsed:
                return parsed
        except json.JSONDecodeError:
            pass

        # Fallback default struct if LLM unparseable
        return {
            "characters": [
                {"name": "Người kể chuyện", "gender": "male", "tone": "Trầm tĩnh", "assigned_voice": "vi_VN-viss-low.onnx"}
            ],
            "world": {
                "locations": ["Bối cảnh câu chuyện"],
                "era": "Cổ đại"
            }
        }

    def analyze_project_story(self, project: Project) -> Dict[str, Any]:
        project_dir = project.project_dir
        cleaned_file = project_dir / "story" / "cleaned.txt"
        if not cleaned_file.exists():
            raise FileNotFoundError(f"Cleaned story file not found: {cleaned_file}")

        text = cleaned_file.read_text(encoding="utf-8")

        # 1. Split Chapters
        chapters = self.split_chapters(text)
        chapters_dir = project_dir / "story" / "chapters"
        chapters_dir.mkdir(parents=True, exist_ok=True)

        for chap in chapters:
            c_file = chapters_dir / f"chapter_{chap['chapter_index']:03d}.txt"
            c_file.write_text(chap["content"], encoding="utf-8")

        # 2. Extract Entities & World Context
        analysis = self.extract_entities_and_world(text)

        # Save characters.json
        char_file = project_dir / "characters" / "characters.json"
        char_file.parent.mkdir(parents=True, exist_ok=True)
        with open(char_file, "w", encoding="utf-8") as f:
            json.dump(analysis.get("characters", []), f, indent=2, ensure_ascii=False)

        # Save world.json
        world_file = project_dir / "story" / "world.json"
        with open(world_file, "w", encoding="utf-8") as f:
            json.dump(analysis.get("world", {}), f, indent=2, ensure_ascii=False)

        # Save timeline.json metadata
        timeline_meta = {
            "total_chapters": len(chapters),
            "chapters": [{"index": c["chapter_index"], "title": c["title"]} for c in chapters]
        }
        timeline_file = project_dir / "timeline" / "timeline.json"
        timeline_file.parent.mkdir(parents=True, exist_ok=True)
        with open(timeline_file, "w", encoding="utf-8") as f:
            json.dump(timeline_meta, f, indent=2, ensure_ascii=False)

        # Update Project Meta
        project.data["characters"] = analysis.get("characters", [])
        project.data["story"]["status"] = "ANALYZED"
        project.save()

        return analysis
