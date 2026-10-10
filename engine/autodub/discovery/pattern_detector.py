import re
import logging
from typing import List, Dict, Any, Optional

logger = logging.getLogger(__name__)

class PatternDetector:
    """Detects structural URL patterns from a sample list of discovered chapter links."""

    @staticmethod
    def detect_pattern(discovered_links: List[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
        """Analyzes URLs of discovered chapters to find a parameter replacement pattern."""
        if len(discovered_links) < 2:
            logger.warning("Not enough chapter links to determine URL pattern.")
            return None

        # Extract URLs and numbers
        samples = []
        for item in discovered_links:
            num = item.get("chapterNumber")
            url = item.get("url", "")
            if num is not None and url:
                samples.append((int(num) if isinstance(num, (int, float)) and float(num).is_integer() else num, url))

        if not samples:
            return None

        # Sort samples by chapter number
        samples.sort(key=lambda x: x[0])
        highest = samples[-1][0]
        lowest = samples[0][0]

        # Try to find common template pattern across sample URLs
        # Replace occurrences of chapter number in URL with {number}
        patterns_found = {}
        for num, url in samples:
            num_str = str(num)
            # Match number in URL preceded by boundary/dash/slash
            # E.g. /chuong-1294 or /chapter/1294 or ?id=1294
            # Also check zero padding e.g. 0001
            str_pattern = re.sub(rf'(?<=[/_\-=?])0*{num_str}(?=[/_\-&]|$)', '{number}', url)
            if str_pattern != url:
                patterns_found[str_pattern] = patterns_found.get(str_pattern, 0) + 1

        if not patterns_found:
            # Secondary check: general regex replacement of trailing numbers
            for num, url in samples:
                str_pattern = re.sub(r'(\d+)(?=[^0-9]*$)', '{number}', url)
                if str_pattern != url:
                    patterns_found[str_pattern] = patterns_found.get(str_pattern, 0) + 1

        if not patterns_found:
            return None

        # Pick the most frequent pattern
        best_pattern = max(patterns_found, key=patterns_found.get)

        # Detect padding if any
        has_padding = False
        padding_length = 0
        for num, url in samples:
            m = re.search(r'(?<=[/_\-=?])(0+\d+)(?=[/_\-&]|$)', url)
            if m:
                has_padding = True
                padding_length = len(m.group(1))
                break

        pattern_result = {
            "pattern": best_pattern,
            "parameter": "number",
            "start": lowest,
            "end": highest,
            "step": 1,
            "hasPadding": has_padding,
            "paddingLength": padding_length,
            "sampleCount": len(samples)
        }

        logger.info(f"Pattern Detected: {pattern_result['pattern']} (Range: {lowest} -> {highest})")
        return pattern_result
