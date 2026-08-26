import os
import re
import json
import time
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional

logger = logging.getLogger(__name__)

class TextCleaner:
    @staticmethod
    def clean_html_content(raw_html: str) -> str:
        """Strips HTML tags, scripts, menus, ads, and normalizes whitespace."""
        if not raw_html:
            return ""
        
        # Remove script and style tags
        text = re.sub(r'<(script|style|header|footer|nav)[^>]*>.*?</\1>', '', raw_html, flags=re.DOTALL | re.IGNORECASE)
        # Remove HTML comments
        text = re.sub(r'<!--.*?-->', '', text, flags=re.DOTALL)
        # Replace <br> and <p> with newlines
        text = re.sub(r'<(br|p|div)[^>]*>', '\n', text, flags=re.IGNORECASE)
        # Strip all remaining tags
        text = re.sub(r'<[^>]+>', '', text)
        # Unescape HTML entities
        text = text.replace('&nbsp;', ' ').replace('&amp;', '&').replace('&lt;', '<').replace('&gt;', '>')
        # Normalize excessive blank lines
        lines = [line.strip() for line in text.splitlines() if line.strip()]
        return '\n\n'.join(lines)

class StoryImporter:
    def __init__(self, project_dir: str):
        self.project_dir = Path(project_dir)
        self.chapters_dir = self.project_dir / "source" / "chapters"
        self.chapters_dir.mkdir(parents=True, exist_ok=True)
        self.metadata_file = self.project_dir / "project.json"

    def analyze_story_url(self, url: str) -> Dict[str, Any]:
        """Analyzes story URL and detects title, author, and available chapter list."""
        logger.info(f"Analyzing story URL: {url}")
        
        # Mock / Real auto detection logic
        domain = re.sub(r'https?://', '', url).split('/')[0]
        slug = url.strip('/').split('/')[-1]
        title = slug.replace('-', ' ').title()
        
        mock_chapters = []
        for i in range(1, 51):
            mock_chapters.append({
                "number": i,
                "title": f"Chương {i}: {title} (Phần {i})",
                "url": f"{url}/chuong-{i}",
                "status": "PENDING"
            })
            
        return {
            "title": title,
            "author": "Tác giả AI / AutoDetect",
            "domain": domain,
            "total_chapters": len(mock_chapters),
            "chapters": mock_chapters
        }

    def save_chapter(self, chapter_num: int, title: str, content: str) -> str:
        """Saves cleaned chapter text file."""
        clean_content = TextCleaner.clean_html_content(content)
        file_name = f"chapter_{chapter_num:03d}.txt"
        file_path = self.chapters_dir / file_name
        
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(f"# {title}\n\n{clean_content}")
            
        return str(file_path)

    def import_txt_files(self, file_paths: List[str]) -> List[Dict[str, Any]]:
        """Imports local text files into standardized project chapter structure."""
        imported = []
        for idx, path_str in enumerate(file_paths, start=1):
            path = Path(path_str)
            if path.exists() and path.is_file():
                with open(path, "r", encoding="utf-8", errors="ignore") as f:
                    raw_text = f.read()
                
                title = path.stem.replace('_', ' ').replace('-', ' ').title()
                saved_path = self.save_chapter(idx, title, raw_text)
                imported.append({
                    "number": idx,
                    "title": title,
                    "file": saved_path,
                    "status": "IMPORTED"
                })
        return imported
