import json
from pathlib import Path
from typing import Dict, Any, List, Optional
from autodub.models.project import Project

class StoryMemoryEngine:
    def __init__(self, project: Project):
        self.project = project
        self.project_dir = project.project_dir
        self.summaries_dir = self.project_dir / "story" / "summaries"
        self.summaries_dir.mkdir(parents=True, exist_ok=True)

    def get_character_bible(self) -> List[Dict[str, Any]]:
        char_file = self.project_dir / "characters" / "characters.json"
        if char_file.exists():
            try:
                with open(char_file, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception:
                pass
        return self.project.data.get("characters", [])

    def get_world_bible(self) -> Dict[str, Any]:
        world_file = self.project_dir / "story" / "world.json"
        if world_file.exists():
            try:
                with open(world_file, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception:
                pass
        return {"locations": [], "era": "Unknown"}

    def get_rolling_summary(self, max_words: int = 500) -> str:
        rolling_file = self.summaries_dir / "rolling_summary.txt"
        if rolling_file.exists():
            text = rolling_file.read_text(encoding="utf-8").strip()
            words = text.split()
            if len(words) > max_words:
                return " ".join(words[-max_words:])
            return text
        return ""

    def update_rolling_summary(self, chapter_index: int, chapter_summary: str):
        # Save individual chapter summary
        chap_summary_file = self.summaries_dir / f"summary_ch{chapter_index:03d}.txt"
        chap_summary_file.write_text(chapter_summary.strip(), encoding="utf-8")

        # Append to rolling summary
        current_rolling = self.get_rolling_summary(max_words=2000)
        new_rolling = f"{current_rolling}\n\n[Chương {chapter_index}]: {chapter_summary.strip()}".strip()

        rolling_file = self.summaries_dir / "rolling_summary.txt"
        rolling_file.write_text(new_rolling, encoding="utf-8")

    def build_context_prompt(self, chapter_index: int, chapter_text: str) -> str:
        characters = self.get_character_bible()
        world = self.get_world_bible()
        rolling_summary = self.get_rolling_summary()

        char_lines = []
        for c in characters:
            name = c.get("name", "Unknown")
            gender = c.get("gender", "unknown")
            tone = c.get("tone", "")
            voice = c.get("assigned_voice", "")
            char_lines.append(f"- {name} (Giới tính: {gender}, Giọng: {voice}, Tính cách: {tone})")
        char_str = "\n".join(char_lines) if char_lines else "- Chưa có thông tin"

        locs = ", ".join(world.get("locations", [])) or "Chưa rõ"
        era = world.get("era", "Cổ đại")

        prompt = f"""
=== BỘ NHỚ CÂU CHUYỆN (STORY MEMORY BIBLE) ===

1. HỒ SƠ NHÂN VẬT (CHARACTER BIBLE):
{char_str}

2. BỐI CẢNH THẾ GIỚI (WORLD BIBLE):
- Địa danh: {locs}
- Thời kỳ: {era}

3. TÓM TẮT DIỄN BIẾN TRƯỚC ĐÓ (ROLLING SUMMARY):
{rolling_summary if rolling_summary else "Đây là chương đầu tiên."}

=== NỘI DUNG CHƯƠNG {chapter_index} HIỆN TẠI ===
{chapter_text}

=== QUY TẮC CHỐNG LẠC ĐỀ ===
- Giữ đúng tên và tính cách nhân vật ở Hồ sơ Nhân vât.
- Không tự suy diễn các mốc thời gian mâu thuẫn với Tóm tắt diễn biến trước đó.
""".strip()

        return prompt
