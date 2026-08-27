import re
import requests
import logging
from typing import Dict, Any, Tuple

logger = logging.getLogger(__name__)

# Minimum character length of story content to consider a page valid
MIN_CONTENT_LENGTH = 100

class ChapterValidator:
    """Validates chapter URLs by making HTTP requests and verifying content markers."""

    @staticmethod
    def validate_chapter_url(url: str, timeout: int = 10) -> Tuple[str, str]:
        """
        Validates if a URL is a valid chapter page.
        
        Returns:
            Tuple of (status, reason) where status is 'VALID' or 'INVALID'
        """
        if not url or not url.startswith(('http://', 'https://')):
            return "INVALID", "INVALID_URL_SCHEME"

        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        }

        try:
            res = requests.get(url, headers=headers, timeout=timeout, allow_redirects=True)
            
            if res.status_code != 200:
                return "INVALID", f"HTTP_{res.status_code}"

            # Check if redirected to home page or main story index
            if res.history:
                final_url = res.url.rstrip('/')
                orig_url = url.rstrip('/')
                if final_url != orig_url:
                    # If redirected to main page or different path root
                    if len(final_url.split('/')) < len(orig_url.split('/')):
                        return "INVALID", "REDIRECTED_TO_HOME_OR_INDEX"

            html = res.text
            if not html:
                return "INVALID", "EMPTY_RESPONSE"

            # Check for error page indicators
            lower_html = html.lower()
            if "404 not found" in lower_html or "trang không tồn tại" in lower_html or "error 404" in lower_html:
                return "INVALID", "ERROR_PAGE_404"

            # Check for chapter title or content presence
            # Strip script/style tags
            clean_text = re.sub(r'<(script|style|header|footer|nav)[^>]*>.*?</\1>', '', html, flags=re.DOTALL | re.IGNORECASE)
            clean_text = re.sub(r'<[^>]+>', ' ', clean_text)
            clean_text = re.sub(r'\s+', ' ', clean_text).strip()

            if len(clean_text) < MIN_CONTENT_LENGTH:
                return "INVALID", "CONTENT_TOO_SHORT"

            # Verify chapter content marker presence (chuong/chapter/noi dung/text)
            chapter_markers = [r'chương', r'chapter', r'phần', r'đọc', r'nội dung']
            if not any(re.search(pattern, lower_html) for pattern in chapter_markers):
                return "INVALID", "NO_CHAPTER_MARKER_FOUND"

            return "VALID", "OK"

        except requests.Timeout:
            return "INVALID", "REQUEST_TIMEOUT"
        except requests.RequestException as e:
            return "INVALID", f"NETWORK_ERROR: {str(e)}"
        except Exception as e:
            return "INVALID", f"UNEXPECTED_ERROR: {str(e)}"
