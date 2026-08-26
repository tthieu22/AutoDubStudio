import json
import re
import requests
from pathlib import Path
from typing import Dict, Any, List, Optional
from autodub.models.project import Project

GUTENDEX_API_URL = "https://gutendex.com/books/"
WIKISOURCE_API_VI = "https://vi.wikisource.org/w/api.php"
WIKISOURCE_API_ZH = "https://zh.wikisource.org/w/api.php"

class GutenbergCollector:
    @staticmethod
    def search_books(topic: str = "ghost", language: str = "en", limit: int = 5) -> List[Dict[str, Any]]:
        params = {
            "topic": topic,
            "languages": language,
            "copyright": "false"
        }
        try:
            res = requests.get(GUTENDEX_API_URL, params=params, timeout=10)
            if res.status_code != 200:
                return []
            data = res.json()
            results = []
            for item in data.get("results", [])[:limit]:
                formats = item.get("formats", {})
                txt_url = (
                    formats.get("text/plain; charset=utf-8")
                    or formats.get("text/plain; charset=us-ascii")
                    or formats.get("text/plain")
                )
                if txt_url:
                    author_name = item["authors"][0]["name"] if item.get("authors") else "Unknown"
                    results.append({
                        "id": f"gutenberg_{item['id']}",
                        "source_type": "gutenberg",
                        "title": item.get("title", "Untitled"),
                        "author": author_name,
                        "source_url": txt_url,
                        "license": "public_domain",
                        "language": language
                    })
            return results
        except Exception:
            return []

    @staticmethod
    def fetch_book_text(txt_url: str) -> str:
        try:
            res = requests.get(txt_url, timeout=15)
            res.encoding = 'utf-8'
            return res.text
        except Exception as e:
            raise RuntimeError(f"Failed to fetch Gutenberg text from {txt_url}: {e}")

class WikisourceCollector:
    @staticmethod
    def fetch_page(title: str, language: str = "vi") -> Dict[str, Any]:
        api_url = WIKISOURCE_API_VI if language == "vi" else WIKISOURCE_API_ZH
        params = {
            "action": "query",
            "prop": "revisions",
            "rvprop": "content",
            "format": "json",
            "titles": title
        }
        try:
            res = requests.get(api_url, params=params, timeout=10)
            if res.status_code != 200:
                raise RuntimeError(f"Wikisource API returned status {res.status_code}")
            data = res.json()
            pages = data.get("query", {}).get("pages", {})
            for page_id, page_data in pages.items():
                if page_id == "-1":
                    raise RuntimeError(f"Page '{title}' not found on Wikisource")
                revisions = page_data.get("revisions", [])
                if revisions:
                    raw_content = revisions[0].get("*", "")
                    return {
                        "id": f"wikisource_{page_id}",
                        "source_type": "wikisource",
                        "title": page_data.get("title", title),
                        "author": "Public Domain",
                        "source_url": f"{api_url}?title={title}",
                        "license": "public_domain",
                        "language": language,
                        "raw_content": raw_content
                    }
            raise RuntimeError(f"No content found for '{title}'")
        except Exception as e:
            raise RuntimeError(f"Failed to fetch Wikisource page: {e}")

class StoryCollector:
    def __init__(self, project: Project):
        self.project = project
        self.project_dir = project.project_dir
        self.story_dir = self.project_dir / "story"
        self.source_dir = self.project_dir / "source"
        self.story_dir.mkdir(parents=True, exist_ok=True)
        self.source_dir.mkdir(parents=True, exist_ok=True)

    def collect(self, source_type: str, identifier: str, language: str = "en") -> Dict[str, Any]:
        if source_type.lower() == "gutenberg":
            # identifier is txt_url or search result
            if identifier.startswith("http"):
                txt_url = identifier
                title = "Gutenberg Book"
                author = "Public Domain Author"
            else:
                books = GutenbergCollector.search_books(topic=identifier, language=language, limit=1)
                if not books:
                    raise RuntimeError(f"No Gutenberg book found for topic '{identifier}'")
                book_meta = books[0]
                txt_url = book_meta["source_url"]
                title = book_meta["title"]
                author = book_meta["author"]

            raw_text = GutenbergCollector.fetch_book_text(txt_url)
            meta = {
                "source_type": "gutenberg",
                "source_url": txt_url,
                "title": title,
                "author": author,
                "license": "public_domain",
                "language": language,
                "status": "FETCHED"
            }

        elif source_type.lower() == "wikisource":
            wiki_meta = WikisourceCollector.fetch_page(title=identifier, language=language)
            raw_text = wiki_meta.pop("raw_content")
            meta = wiki_meta
            meta["status"] = "FETCHED"

        else:
            raise ValueError(f"Unsupported source type: '{source_type}'. Supported: 'gutenberg', 'wikisource'")

        # Save artifacts
        original_txt_path = self.story_dir / "original.txt"
        with open(original_txt_path, "w", encoding="utf-8") as f:
            f.write(raw_text)

        source_json_path = self.source_dir / "story_source.json"
        with open(source_json_path, "w", encoding="utf-8") as f:
            json.dump(meta, f, indent=2, ensure_ascii=False)

        # Update Project Data
        self.project.data["story"] = meta
        self.project.save()

        return meta
