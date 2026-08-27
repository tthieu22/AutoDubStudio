import json
import logging
import requests
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)

OLLAMA_URL = "http://127.0.0.1:11434/api/generate"

class AIAssistant:
    """AI Assistant (Qwen 2.5) for analyzing complex HTML structures and structural pattern suggestions."""

    def __init__(self, ollama_url: str = OLLAMA_URL, model: str = "qwen2.5:7b-instruct"):
        self.ollama_url = ollama_url
        self.model = model

    def analyze_html_structure(self, url: str, html_snippet: str) -> Dict[str, Any]:
        """
        Sends truncated HTML snippet to Qwen 2.5 to analyze chapter list structure,
        selectors, pagination buttons, and URL pattern template.
        """
        # Limit snippet size to ~4KB for AI context
        truncated_snippet = html_snippet[:4000]

        prompt = f"""You are a Web Scraping & HTML Structure Analyzer AI.
Analyze the following HTML snippet from story URL: {url}

HTML Snippet:
```html
{truncated_snippet}
```

Respond STRICTLY in JSON format with no additional text:
{{
  "chapterSelector": "CSS selector or regex for chapter links (e.g. '.chapter-list a')",
  "paginationSelector": "CSS selector for pagination/next page",
  "loadMoreSelector": "CSS selector for load more button/link",
  "urlPattern": "URL template containing {{number}} placeholder if applicable (e.g. '{url}/chuong-{{number}}')",
  "confidence": 0.85
}}
"""

        payload = {
            "model": self.model,
            "prompt": prompt,
            "stream": False,
            "options": {
                "temperature": 0.1
            }
        }

        try:
            res = requests.post(self.ollama_url, json=payload, timeout=20)
            if res.status_code == 200:
                resp_json = res.json()
                raw_response = resp_json.get("response", "").strip()
                # Parse JSON block
                json_match = re.search(r'\{.*\}', raw_response, re.DOTALL)
                if json_match:
                    parsed = json.loads(json_match.group(0))
                    logger.info(f"AI HTML Analysis complete. Confidence={parsed.get('confidence', 0)}")
                    return parsed
        except Exception as e:
            logger.warning(f"AI Assistant unavailable or timed out: {e}")

        # Fallback response if AI call fails
        return {
            "chapterSelector": "",
            "paginationSelector": "",
            "loadMoreSelector": "",
            "urlPattern": "",
            "confidence": 0.0
        }
