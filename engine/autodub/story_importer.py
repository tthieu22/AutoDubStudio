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
        """Strips HTML tags, scripts, menus, ads, webnovel chrome, and normalizes whitespace."""
        if not raw_html:
            return ""

        text = raw_html
        if '<' in raw_html and '>' in raw_html:
            try:
                from bs4 import BeautifulSoup, Comment
                soup = BeautifulSoup(raw_html, 'html.parser')

                for comment in soup.find_all(string=lambda t: isinstance(t, Comment)):
                    comment.extract()

                for tag in soup.find_all(['script', 'style', 'noscript', 'iframe', 'header', 'footer', 'nav', 'aside', 'form', 'svg', 'button', 'input', 'select', 'option']):
                    tag.decompose()

                CONTENT_SELECTORS = [
                    '#chapter-c', '.chapter-c', '#chapter-content', '.chapter-content',
                    '#cha-content', '.cha-content', '#content-container', '.content-container',
                    '.reading-content', '#reading-content', '.chapter-text', '#chapter-text',
                    '.v-content', '#v-content', '#chapter-body', '.chapter-body',
                    '[itemprop="articleBody"]', '#box-chap', '.box-chap', 'article'
                ]

                target = None
                for sel in CONTENT_SELECTORS:
                    found = soup.select_one(sel)
                    if found and len(found.get_text().strip()) > 50:
                        target = found
                        break

                if not target:
                    target = soup.body or soup

                UNWANTED_KEYWORDS = [
                    'ads', 'advertisement', 'google-ad', 'banner',
                    'nav', 'pagination', 'chapter-nav', 'chap-nav', 'btn-chap', 'btn-chapter', 'chapter-action',
                    'report', 'error-report', 'bao-loi', 'baoloi',
                    'setting', 'toolbar', 'option', 'font-setting', 'color-setting', 'reading-control', 'reading-setting',
                    'recommend', 'collection', 'sidebar', 'modal', 'popup', 'dialog', 'comment'
                ]

                for elem in target.find_all(True):
                    elem_id = str(elem.get('id', '')).lower()
                    elem_classes = ' '.join(elem.get('class', [])).lower() if isinstance(elem.get('class'), list) else str(elem.get('class', '')).lower()
                    combined = f"{elem_id} {elem_classes}"
                    if any(kw in combined for kw in UNWANTED_KEYWORDS):
                        elem.decompose()

                for br in target.find_all(['br', 'p', 'div']):
                    br.insert_after(soup.new_string('\n'))

                text = target.get_text()
            except Exception as e:
                logger.warning(f"BeautifulSoup parsing fallback due to: {e}")
                text = re.sub(r'<(script|style|header|footer|nav)[^>]*>.*?</\1>', '', raw_html, flags=re.DOTALL | re.IGNORECASE)
                text = re.sub(r'<!--.*?-->', '', text, flags=re.DOTALL)
                text = re.sub(r'<(br|p|div)[^>]*>', '\n', text, flags=re.IGNORECASE)
                text = re.sub(r'<[^>]+>', '', text)

        text = text.replace('&nbsp;', ' ').replace('&amp;', '&').replace('&lt;', '<').replace('&gt;', '>')

        NOISE_PATTERNS = [
            r'^\s*chương\s*(trước|sau)\s*$',
            r'^\s*báo\s*lỗi\s*(chương)?\s*$',
            r'^\s*tài\s*khoản\s*$',
            r'^\s*đăng\s*(nhập|ký)\s*$',
            r'^\s*bảng\s*tác\s*vụ\s*đọc.*$',
            r'^\s*ds\s*chương\s*$',
            r'^\s*cấu\s*hình\s*$',
            r'^\s*màu\s*nền\s*$',
            r'^\s*font\s*chữ\s*$',
            r'^\s*kiểu\s*chữ\s*$',
            r'^\s*khôi\s*phục\s*mặc\s*định\s*$',
            r'tuyển\s*tập\s*truyện',
            r'top\s*truyện\s*full',
            r'list\s*truyện',
            r'truyện\s*ngôn\s*tình',
            r'truyện\s*xuyên\s*không',
            r'^\s*mục\s*lục\s*$',
            r'^\s*trang\s*chủ\s*$',
            r'^[^\w\s]+$',
            r'^(palatino|bookerly|be vietnam|montserrat|arial|times new roman)$',
            r'\|\s*(webnovel\.vn|truyenfull|tangthuvien|metruyenchu|bachngocsach|truyenchu)'
        ]

        lines = []
        for line in text.splitlines():
            line_s = line.strip()
            if not line_s:
                continue
            if any(re.search(p, line_s, re.IGNORECASE) for p in NOISE_PATTERNS):
                continue
            lines.append(line_s)

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

        # ── Persist chapters into project.json so the frontend can read them ──
        self._save_chapters_to_project_json(imported_list)

        return imported_list

    def _save_chapters_to_project_json(self, imported_list: List[Dict[str, Any]]):
        """Reads each saved chapter .txt file and writes chapter data with content into project.json."""
        project_json = {}
        if self.metadata_file.exists():
            try:
                project_json = json.loads(self.metadata_file.read_text(encoding="utf-8"))
            except Exception:
                project_json = {}

        existing_chapters = project_json.get("chapters", [])

        for rec in imported_list:
            if rec.get("status") not in ("SUCCESS", "LOW_CONTENT"):
                continue

            file_path = rec.get("file", "")
            content_text = ""
            if file_path and os.path.exists(file_path):
                try:
                    content_text = Path(file_path).read_text(encoding="utf-8")
                    # Remove the "# Title" header line from content
                    if content_text.startswith("# "):
                        content_text = content_text.split("\n", 1)[-1].strip()
                except Exception as e:
                    logger.warning(f"Failed to read chapter file {file_path}: {e}")

            chapter_entry = {
                "id": f"imported-{int(time.time() * 1000)}-{rec['number']}",
                "chapterNumber": rec["number"],
                "title": rec.get("title", f"Chương {rec['number']}"),
                "summary": content_text[:300] + "..." if len(content_text) > 300 else content_text,
                "content": content_text,
                "characters": ["AutoDetect"],
                "scenesCount": 0,
                "sourceFile": file_path,
                "wordCount": rec.get("wordCount", 0),
                "sourceUrl": rec.get("url", "")
            }
            existing_chapters.append(chapter_entry)
            # Small delay to ensure unique IDs
            time.sleep(0.002)

        project_json["chapters"] = existing_chapters
        try:
            self.metadata_file.write_text(
                json.dumps(project_json, indent=2, ensure_ascii=False),
                encoding="utf-8"
            )
            logger.info(f"Saved {len(existing_chapters)} chapters to project.json")
        except Exception as e:
            logger.error(f"Failed to write project.json: {e}")
