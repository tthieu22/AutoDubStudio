import re
import time
import requests
import urllib3
import logging
from pathlib import Path
from typing import Dict, Any, Optional, Callable

from autodub.discovery.link_discovery import LinkDiscovery
from autodub.discovery.pagination_handler import PaginationHandler
from autodub.discovery.pattern_detector import PatternDetector
from autodub.discovery.generator import generate_chapter_urls
from autodub.discovery.validator import ChapterValidator
from autodub.discovery.ai_assistant import AIAssistant
from autodub.discovery.registry import ChapterRegistry

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
logger = logging.getLogger(__name__)

# Configurable Safety Limits
DEFAULT_MAX_CHAPTERS = 3000
DEFAULT_MAX_REQUESTS = 100
DEFAULT_MAX_PAGINATION_DEPTH = 10
DEFAULT_DELAY_MS = 100
DEFAULT_CONCURRENCY = 5

def safe_fetch_html(url: str, timeout: int = 12) -> Optional[str]:
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
        "Accept-Language": "vi-VN,vi;q=0.9,en-US;q=0.8,en;q=0.7",
    }
    try:
        res = requests.get(url, headers=headers, timeout=timeout, verify=True)
        if res.status_code == 200:
            res.encoding = res.apparent_encoding or 'utf-8'
            return res.text
    except Exception as e:
        logger.warning(f"Verify SSL failed for {url}, trying verify=False: {e}")
    try:
        res = requests.get(url, headers=headers, timeout=timeout, verify=False)
        if res.status_code == 200:
            res.encoding = res.apparent_encoding or 'utf-8'
            return res.text
    except Exception as e:
        logger.error(f"Failed to fetch HTML from {url}: {e}")
    return None

class AdaptiveDiscoveryEngine:
    """Core Adaptive Chapter Discovery Engine for Story Mode."""

    def __init__(
        self,
        story_url: str,
        registry_file: Optional[Path] = None,
        max_chapters: int = DEFAULT_MAX_CHAPTERS,
        max_requests: int = DEFAULT_MAX_REQUESTS,
        delay_ms: int = DEFAULT_DELAY_MS,
        progress_callback: Optional[Callable[[Dict[str, Any]], None]] = None
    ):
        self.story_url = story_url
        self.registry = ChapterRegistry(story_url, registry_file=registry_file)
        self.max_chapters = max_chapters
        self.max_requests = max_requests
        self.delay_ms = delay_ms
        self.progress_callback = progress_callback
        self.request_count = 0
        self.ai_assistant = AIAssistant()

    def _emit_progress(self, stage: str, percent: int, message: str, extra: Optional[Dict[str, Any]] = None):
        """Helper to emit real-time progress events."""
        data = {
            "event": "discovery_progress",
            "stage": stage,
            "percent": percent,
            "message": message,
            "timestamp": time.time(),
            "registry": self.registry.to_dict()
        }
        if extra:
            data.update(extra)
        if self.progress_callback:
            self.progress_callback(data)
        logger.info(f"[{stage}] {percent}% - {message}")

    def run(self) -> Dict[str, Any]:
        self._emit_progress("START", 5, f"Bắt đầu kết nối website: {self.story_url}")

        # STEP 1: Normalize single-chapter URL to parent story URL if applicable
        target_url = self.story_url
        input_pattern = None

        chap_match = re.search(r'(/(?:chuong|chapter|chap|ch)[-_\s\.]*)(\d+)(/?.*)$', self.story_url, re.IGNORECASE)
        if chap_match:
            prefix, num_str, suffix = chap_match.groups()
            input_pattern = self.story_url.replace(f"{prefix}{num_str}{suffix}", f"{prefix}{{number}}{suffix}")
            parent_path = self.story_url[:chap_match.start()]
            if parent_path.startswith(('http://', 'https://')):
                target_url = parent_path.rstrip('/') + '/'
            self._emit_progress("NORMALIZE", 10, f"Đã chuẩn hóa URL về trang truyện gốc: {target_url}")

        # Fetch HTML from main story page (and input chapter URL if different)
        urls_to_fetch = [target_url]
        if target_url != self.story_url:
            urls_to_fetch.append(self.story_url)

        html_content = ""
        for u in urls_to_fetch:
            self._emit_progress("HTTP_FETCH", 15, f"Đang tải dữ liệu HTML từ {u}...")
            text = safe_fetch_html(u)
            self.request_count += 1
            if text:
                html_content += "\n" + text
                self._emit_progress("HTTP_SUCCESS", 20, f"Đã tải xong HTML ({len(text):,} bytes)")
            else:
                self._emit_progress("HTTP_WARN", 20, f"Cảnh báo: Không thể tải HTML từ {u}")

        if not html_content:
            self._emit_progress("ERROR", 100, f"Lỗi: Không thể kết nối hoặc tải HTML từ URL {self.story_url}")
            return self.registry.to_dict()

        # STEP 2: HTML Link Discovery
        self._emit_progress("FETCH", 25, "Đang phân tích link chapter trong HTML...")
        initial_links = LinkDiscovery.extract_chapter_links(target_url, html_content)

        for item in initial_links:
            self.registry.add_or_update_chapter(
                number=item["chapterNumber"],
                title=item["chapterTitle"],
                url=item["url"],
                discovered_by="HTML_LINK"
            )
        if "HTML_LINK" not in self.registry.discovery_methods:
            self.registry.discovery_methods.append("HTML_LINK")

        # STEP 3: Pagination / Load-More Discovery
        self._emit_progress("PAGINATION", 45, "Phát hiện phân trang & Xem thêm...")
        pagination_info = PaginationHandler.detect_pagination_and_api(self.story_url, html_content)

        if pagination_info["hasLoadMore"] and pagination_info["nextPageUrls"]:
            if "LOAD_MORE" not in self.registry.discovery_methods:
                self.registry.discovery_methods.append("LOAD_MORE")

            # Fetch extra pages up to pagination depth limit
            for page_url in pagination_info["nextPageUrls"][:DEFAULT_MAX_PAGINATION_DEPTH]:
                if self.request_count >= self.max_requests:
                    logger.warning("DISCOVERY_LIMIT_REACHED: Max requests limit hit.")
                    break
                time.sleep(self.delay_ms / 1000.0)
                try:
                    p_html = safe_fetch_html(page_url)
                    self.request_count += 1
                    if p_html:
                        extra_links = LinkDiscovery.extract_chapter_links(self.story_url, p_html)
                        for item in extra_links:
                            self.registry.add_or_update_chapter(
                                number=item["chapterNumber"],
                                title=item["chapterTitle"],
                                url=item["url"],
                                discovered_by="LOAD_MORE"
                            )
                except Exception:
                    pass

        # STEP 4: URL Pattern Detection
        self._emit_progress("PATTERN", 65, "Phân tích quy luật URL Pattern...")
        pattern_res = PatternDetector.detect_pattern(self.registry.chapters)

        if not pattern_res and input_pattern:
            pattern_res = {
                "pattern": input_pattern,
                "parameter": "number",
                "start": self.registry.lowest_chapter or 1,
                "end": self.registry.highest_chapter or 50,
                "step": 1
            }

        if pattern_res:
            self.registry.pattern = pattern_res["pattern"]
            if "URL_PATTERN" not in self.registry.discovery_methods:
                self.registry.discovery_methods.append("URL_PATTERN")

            # STEP 5: Pattern Validation (Prob sampling)
            self._emit_progress("PATTERN_VALIDATION", 75, "Kiểm tra tính hợp lệ của URL Pattern...")
            sample_urls = [
                pattern_res["pattern"].replace("{number}", str(pattern_res["start"])),
                pattern_res["pattern"].replace("{number}", str(pattern_res["end"]))
            ]
            valid_samples = 0
            for s_url in sample_urls:
                st, _ = ChapterValidator.validate_chapter_url(s_url)
                if st == "VALID":
                    valid_samples += 1

            if valid_samples >= 1:
                self.registry.pattern_status = "VALIDATED"
                self.registry.confidence = "HIGH"
            else:
                self.registry.pattern_status = "INVALID"
                self.registry.confidence = "LOW"

            # STEP 6: Deterministic Chapter Candidate Generation
            if self.registry.pattern_status == "VALIDATED":
                self._emit_progress("GENERATION", 85, "Sinh ứng viên URL bằng hàm toán học Deterministic...")
                candidates = generate_chapter_urls(
                    pattern=pattern_res["pattern"],
                    start=pattern_res["start"],
                    end=min(pattern_res["end"], self.max_chapters),
                    step=pattern_res["step"],
                    has_padding=pattern_res.get("hasPadding", False),
                    padding_length=pattern_res.get("paddingLength", 0)
                )

                for cand in candidates:
                    self.registry.add_or_update_chapter(
                        number=cand["number"],
                        title=cand["title"],
                        url=cand["url"],
                        discovered_by="PATTERN"
                    )

        # STEP 7: AI Assistant Fallback if confidence is LOW
        if self.registry.confidence == "LOW":
            self._emit_progress("AI_FALLBACK", 90, "Đang dùng Qwen 2.5 phân tích cấu trúc HTML phức tạp...")
            ai_res = self.ai_assistant.analyze_html_structure(self.story_url, html_content)
            if ai_res.get("urlPattern"):
                self.registry.pattern = ai_res["urlPattern"]
                self.registry.confidence = "MEDIUM"

        # STEP 8: Final Candidate Validation (Sample Validation)
        self._emit_progress("VALIDATION", 95, "Xác minh các chương phát hiện...")
        for chap in self.registry.chapters[:10]:  # Quick sample validation
            if chap["status"] == "PENDING":
                st, _ = ChapterValidator.validate_chapter_url(chap["url"])
                chap["status"] = st

        self.registry.recalculate_bounds()
        self.registry.save()

        self._emit_progress("DONE", 100, f"Phát hiện hoàn tất! Đã tìm thấy {len(self.registry.chapters)} chương.")
        return self.registry.to_dict()
