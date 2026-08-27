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

    def analyze_story_url(self, url: str, progress_callback=None) -> Dict[str, Any]:
        """Analyzes story URL using Adaptive Discovery Engine and returns Chapter Registry."""
        logger.info(f"Analyzing story URL with Adaptive Discovery Engine: {url}")
        from autodub.discovery.engine import AdaptiveDiscoveryEngine

        registry_file = self.project_dir / "story" / "chapter_registry.json"
        engine = AdaptiveDiscoveryEngine(
            story_url=url,
            registry_file=registry_file,
            progress_callback=progress_callback
        )
        registry_data = engine.run()

        slug = url.strip('/').split('/')[-1]
        title = slug.replace('-', ' ').title()

        return {
            "title": title,
            "author": "AutoDetect Website",
            "domain": re.sub(r'https?://', '', url).split('/')[0],
            "total_chapters": registry_data.get("totalCandidates", 0),
            "chapters": registry_data.get("chapters", []),
            "registry": registry_data
        }

    def save_chapter(self, chapter_num: int, title: str, content: str) -> str:
        """Saves cleaned chapter text file."""
        clean_content = TextCleaner.clean_html_content(content)
        file_name = f"chapter_{chapter_num:03d}.txt"
        file_path = self.chapters_dir / file_name
        
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(f"# {title}\n\n{clean_content}")
            
        return str(file_path)

    def download_and_import_chapters(
        self,
        chapters: List[Dict[str, Any]],
        delay_ms: int = 200,
        progress_callback: Optional[Any] = None
    ) -> List[Dict[str, Any]]:
        """Downloads, cleans, validates, and saves selected chapter URLs to source/chapters/."""
        import requests
        import time
        from urllib.parse import urlparse

        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        }

        imported_list = []
        total = len(chapters)

        for idx, item in enumerate(chapters, start=1):
            num = item.get("number", idx)
            title = item.get("title", f"Chương {num}")
            url = item.get("url", "")

            if progress_callback:
                progress_callback({
                    "event": "chapter_import_progress",
                    "stage": "CHAPTER_PROCESSING",
                    "current": idx,
                    "total": total,
                    "percent": round((idx / total) * 100),
                    "currentChapter": title,
                    "url": url
                })

            # SSRF Safety Check
            parsed = urlparse(url)
            hostname = (parsed.hostname or "").lower()
            if hostname in ["localhost", "127.0.0.1", "0.0.0.0"] or hostname.startswith(("192.168.", "10.", "172.16.")):
                logger.warning(f"SSRF blocked for dangerous URL: {url}")
                continue

            raw_html = ""
            status = "SUCCESS"
            error_msg = None

            try:
                time.sleep(delay_ms / 1000.0)
                res = requests.get(url, headers=headers, timeout=12)
                if res.status_code == 200:
                    raw_html = res.text
                else:
                    status = "FAILED"
                    error_msg = f"HTTP_{res.status_code}"
            except Exception as e:
                status = "FAILED"
                error_msg = str(e)

            clean_text = TextCleaner.clean_html_content(raw_html) if raw_html else ""
            word_count = len(clean_text.split())

            if word_count < 30 and status == "SUCCESS":
                status = "LOW_CONTENT"

            saved_file = ""
            if clean_text:
                saved_file = self.save_chapter(num, title, clean_text)

            chapter_record = {
                "number": num,
                "title": title,
                "url": url,
                "file": saved_file,
                "wordCount": word_count,
                "status": status,
                "error": error_msg
            }
            imported_list.append(chapter_record)

            if progress_callback:
                progress_callback({
                    "event": "chapter_import_progress",
                    "stage": "CHAPTER_COMPLETED",
                    "current": idx,
                    "total": total,
                    "percent": int((idx / total) * 100),
                    "record": chapter_record
                })

        logger.info(f"Successfully imported {len(imported_list)} chapters to {self.chapters_dir}")
        return imported_list
