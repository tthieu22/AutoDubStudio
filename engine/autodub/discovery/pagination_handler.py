import re
import logging
from urllib.parse import urljoin
from typing import List, Dict, Any, Optional

logger = logging.getLogger(__name__)

LOAD_MORE_TEXT_PATTERNS = [
    re.compile(r'(xem\s+thêm|load\s+more|more\s+chapters|xem\s+tất\s+cả|trang\s+sau|next\s+page)', re.IGNORECASE),
    re.compile(r'class=["\'][^"\']*(load-more|btn-more|pagination|view-more)[^"\']*["\']', re.IGNORECASE),
    re.compile(r'data-(api|url|page|ajax)=["\']([^"\']+)["\']', re.IGNORECASE)
]

class PaginationHandler:
    """Detects load-more buttons, pagination links, and API endpoints for chapter lists."""

    @staticmethod
    def detect_pagination_and_api(base_url: str, html_content: str) -> Dict[str, Any]:
        """Scans HTML for pagination or ajax endpoints used for loading more chapters."""
        result = {
            "hasLoadMore": False,
            "nextPageUrls": [],
            "apiEndpoints": [],
            "selectors": []
        }

        # 1. Check for explicit hrefs in pagination containers
        pagination_links = re.findall(
            r'<a\s+[^>]*href=["\']([^"\']+)["\'][^>]*>(.*?)</a>',
            html_content,
            re.IGNORECASE | re.DOTALL
        )

        for href, text in pagination_links:
            clean_text = re.sub(r'<[^>]+>', '', text).strip()
            for pattern in LOAD_MORE_TEXT_PATTERNS:
                if pattern.search(clean_text) or pattern.search(href):
                    full_url = urljoin(base_url, href)
                    if full_url not in result["nextPageUrls"]:
                        result["nextPageUrls"].append(full_url)
                        result["hasLoadMore"] = True

        # 2. Check for data attributes containing AJAX URLs
        data_ajax_matches = re.findall(r'data-(?:ajax|url|endpoint|api)=["\']([^"\']+)["\']', html_content, re.IGNORECASE)
        for endpoint in data_ajax_matches:
            full_api = urljoin(base_url, endpoint)
            if full_api not in result["apiEndpoints"]:
                result["apiEndpoints"].append(full_api)
                result["hasLoadMore"] = True

        # 3. Check common pagination URL patterns (e.g. ?page=2 or /page/2)
        page_num_matches = re.findall(r'href=["\']([^"\']*(?:page|trang)[=\/]\d+[^"\']*)["\']', html_content, re.IGNORECASE)
        for page_url in page_num_matches:
            full_page = urljoin(base_url, page_url)
            if full_page not in result["nextPageUrls"]:
                result["nextPageUrls"].append(full_page)

        logger.info(f"Pagination Detection: HasLoadMore={result['hasLoadMore']}, NextPages={len(result['nextPageUrls'])}, APIs={len(result['apiEndpoints'])}")
        return result
