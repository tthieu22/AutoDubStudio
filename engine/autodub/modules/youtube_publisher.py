import json
import requests
from pathlib import Path
from typing import Dict, Any, List, Optional
from autodub.models.project import Project
from autodub.pipeline.task_state import TaskStatus
from autodub.modules.llamacpp_client import strip_think_tags

OLLAMA_GENERATE_URL = "http://localhost:11434/api/generate"

class YouTubePublisher:
    def __init__(self, project: Project, model_name: str = "qwen2.5-3b-instruct"):
        self.project = project
        self.project_dir = project.project_dir
        self.model_name = model_name

    def generate_youtube_metadata(self) -> Dict[str, Any]:
        story_meta = self.project.data.get("story", {})
        title = story_meta.get("title") or self.project.data.get("name", "Story Video")
        author = story_meta.get("author", "Unknown")

        prompt = f"""
Bạn là chuyên gia SEO và Marketing YouTube. Hãy tạo tiêu đề, mô tả và từ khóa đăng video YouTube cho bộ truyện sau:
Tên truyện: {title}
Tác giả: {author}

Trả về duy nhất định dạng JSON:
{{
  "title": "Tiêu đề video YouTube hấp dẫn (dưới 100 ký tự)",
  "description": "Mô tả video cuốn hút kèm hashtag",
  "tags": ["truyện cổ tích", "audiobook", "truyện ma"],
  "privacy_status": "private"
}}
"""
        payload = {
            "model": self.model_name,
            "prompt": prompt,
            "stream": False,
            "format": "json"
        }
        try:
            res = requests.post(OLLAMA_GENERATE_URL, json=payload, timeout=20)
            if res.status_code == 200:
                raw_text = res.json().get("response", "{}")
                parsed = json.loads(strip_think_tags(raw_text))
                if "title" in parsed:
                    return parsed
        except Exception:
            pass

        return {
            "title": f"[Audiobook] {title} - Full HD Story",
            "description": f"Nghe truyện cổ tích {title} của tác giả {author}. Đăng ký kênh để theo dõi các tập mới nhất!\n\n#Audiobook #AutoDubStudio #Story",
            "tags": ["audiobook", "truyen audio", "auto dub studio"],
            "privacy_status": "private"
        }

    def publish_video(self, privacy_status: str = "private") -> Dict[str, Any]:
        final_video = self.project_dir / "output" / "final.mp4"
        if not final_video.exists():
            raise FileNotFoundError(f"Final render video not found: {final_video}")

        meta = self.generate_youtube_metadata()
        meta["privacy_status"] = privacy_status

        # Save metadata artifact
        pub_file = self.project_dir / "reviews" / "youtube_publish_metadata.json"
        pub_file.parent.mkdir(parents=True, exist_ok=True)
        with open(pub_file, "w", encoding="utf-8") as f:
            json.dump(meta, f, indent=2, ensure_ascii=False)

        # Mock publish success
        result = {
            "status": "SCHEDULED" if privacy_status == "scheduled" else "PUBLISHED_DRAFT",
            "video_id": f"yt_mock_{self.project.data.get('project_id')[:8]}",
            "metadata": meta
        }

        self.project.data["story"]["status"] = "PUBLISHED"
        self.project.save()

        return result
