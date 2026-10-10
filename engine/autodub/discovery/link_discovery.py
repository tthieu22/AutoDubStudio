import re
import logging
from urllib.parse import urljoin, urlparse
from typing import List, Dict, Any, Optional

logger = logging.getLogger(__name__)

# Regular expressions for matching chapter numbers and titles
CHAPTER_NUM_PATTERNS = [
    re.compile(r'(?:chuong|chapter|capitulo|capítulo|chap|ch)[-_\s\.]*(\d+(?:\.\d+)?)', re.IGNORECASE),
    re.compile(r'(\d+)', re.IGNORECASE)
]

class LinkDiscovery:
    """Extracts chapter links and metadata from raw HTML content."""

    @staticmethod
    def normalize_url(base_url: str, href: str) -> str:
        """Converts relative URLs to absolute URLs and cleans trailing anchors/params if needed."""
        if not href or href.startswith('javascript:') or href.startswith('#'):
            return ""
        full_url = urljoin(base_url, href.strip())
        # Remove fragment
        parsed = urlparse(full_url)
        clean_url = parsed._replace(fragment="").geturl()
        return clean_url

    @staticmethod
    def extract_chapter_number(text: str, href: str) -> Optional[float]:
        """Tries to extract a numeric chapter number from anchor text or href URL."""
        # Try matching text first, then href
        for target in [text, href]:
            if not target:
                continue
            for pattern in CHAPTER_NUM_PATTERNS:
                match = pattern.search(target)
                if match:
                    try:
                        val = float(match.group(1))
                        # If integer, return int-equivalent float
                        return int(val) if val.is_integer() else val
                    except ValueError:
                        continue
        return None

    @classmethod
    def extract_chapter_links(cls, base_url: str, html_content: str) -> List[Dict[str, Any]]:
        """Parses HTML anchor tags to find potential chapter links with titles and numbers."""
        discovered = []
        seen_urls = set()

        # Regex for finding all <a> tags with href and inner text
        a_tag_pattern = re.compile(
            r'<a\s+[^>]*href=["\']([^"\']+)["\'][^>]*>(.*?)</a>',
            re.IGNORECASE | re.DOTALL
        )

        for match in a_tag_pattern.finditer(html_content):
            raw_href, inner_html = match.groups()
            clean_url = cls.normalize_url(base_url, raw_href)
            if not clean_url or clean_url in seen_urls:
                continue

            # Strip nested HTML tags to get raw text title
            raw_text = re.sub(r'<[^>]+>', ' ', inner_html).strip()
            # Normalize internal whitespace
            title_text = re.sub(r'\s+', ' ', raw_text)

            # Check if this link looks like a chapter link
            chap_num = cls.extract_chapter_number(title_text, clean_url)
            if chap_num is None:
                continue

            # Basic filtering: skip links to main domain root or non-chapter sections
            parsed = urlparse(clean_url)
            lower_url = clean_url.lower()
            if parsed.path in ["", "/", "/index.html"] or lower_url.startswith(("tel:", "mailto:", "javascript:")):
                continue
            if any(junk in lower_url for junk in ["/blog/", "/tags/", "/tim-truyen/", "online.gov.vn", "cdn-cgi", "facebook", "twitter"]):
                continue

            seen_urls.add(clean_url)
            discovered.append({
                "chapterNumber": chap_num,
                "chapterTitle": title_text or f"Chương {chap_num}",
                "url": clean_url,
                "discoveredBy": "HTML_LINK",
                "validationStatus": "PENDING"
            })

        # Sort by chapter number
        discovered.sort(key=lambda x: x["chapterNumber"])
        logger.info(f"Discovered {len(discovered)} chapter links from HTML")
        return discovered
