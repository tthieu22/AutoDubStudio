import json
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional

logger = logging.getLogger(__name__)

class ChapterRegistry:
    """Manages chapter candidates, status tracking, deduplication, and persistent checkpointing."""

    def __init__(self, story_url: str, registry_file: Optional[Path] = None):
        self.story_url = story_url
        self.registry_file = registry_file
        self.pattern: Optional[str] = None
        self.pattern_status: str = "PENDING"  # PENDING | VALIDATED | INVALID
        self.confidence: str = "LOW"  # LOW | MEDIUM | HIGH
        self.highest_chapter: int = 0
        self.lowest_chapter: int = 0
        self.chapters: List[Dict[str, Any]] = []
        self.missing_chapters: List[int] = []
        self.discovery_methods: List[str] = []

        if registry_file and registry_file.exists():
            self.load()

    def add_or_update_chapter(
        self,
        number: int,
        title: str,
        url: str,
        discovered_by: str = "HTML_LINK",
        status: str = "PENDING"
    ):
        """Adds or updates a chapter entry, preserving multiple discoveredBy methods and deduplicating."""
        existing = next((c for c in self.chapters if c["number"] == number or c["url"] == url), None)

        if existing:
            # Add discovery method if not present
            if isinstance(existing.get("discoveredBy"), list):
                if discovered_by not in existing["discoveredBy"]:
                    existing["discoveredBy"].append(discovered_by)
            elif existing.get("discoveredBy") != discovered_by:
                existing["discoveredBy"] = [existing["discoveredBy"], discovered_by]

            # Update status if new status is higher priority (VALID > PENDING)
            if status != "PENDING" or existing["status"] == "PENDING":
                existing["status"] = status
            if title and not existing.get("title"):
                existing["title"] = title
        else:
            self.chapters.append({
                "number": number,
                "title": title or f"Chương {number}",
                "url": url,
                "discoveredBy": [discovered_by] if isinstance(discovered_by, str) else discovered_by,
                "status": status
            })

        self.recalculate_bounds()

    def recalculate_bounds(self):
        """Recalculates lowest, highest, and missing chapters."""
        if not self.chapters:
            self.lowest_chapter = 0
            self.highest_chapter = 0
            self.missing_chapters = []
            return

        self.chapters.sort(key=lambda x: x["number"])
        nums = [c["number"] for c in self.chapters if isinstance(c["number"], (int, float))]
        if nums:
            self.lowest_chapter = int(min(nums))
            self.highest_chapter = int(max(nums))

            # Detect missing integer chapter numbers in sequence
            num_set = set(int(n) for n in nums if float(n).is_integer())
            expected_set = set(range(self.lowest_chapter, self.highest_chapter + 1))
            self.missing_chapters = sorted(list(expected_set - num_set))

    def to_dict(self) -> Dict[str, Any]:
        """Serializes registry to dictionary."""
        self.recalculate_bounds()
        valid_count = sum(1 for c in self.chapters if c.get("status") == "VALID")
        invalid_count = sum(1 for c in self.chapters if c.get("status") == "INVALID")
        pending_count = sum(1 for c in self.chapters if c.get("status") == "PENDING")

        return {
            "storyUrl": self.story_url,
            "pattern": self.pattern,
            "patternStatus": self.pattern_status,
            "confidence": self.confidence,
            "highestChapter": self.highest_chapter,
            "lowestChapter": self.lowest_chapter,
            "totalCandidates": len(self.chapters),
            "validatedCount": valid_count,
            "invalidCount": invalid_count,
            "pendingCount": pending_count,
            "missingChapters": self.missing_chapters,
            "discoveryMethods": self.discovery_methods,
            "chapters": self.chapters
        }

    def save(self):
        """Persists chapter registry to JSON file if path configured."""
        if not self.registry_file:
            return
        self.registry_file.parent.mkdir(parents=True, exist_ok=True)
        with open(self.registry_file, "w", encoding="utf-8") as f:
            json.dump(self.to_dict(), f, indent=2, ensure_ascii=False)
        logger.info(f"Saved ChapterRegistry to {self.registry_file}")

    def load(self):
        """Loads chapter registry from JSON file."""
        if not self.registry_file or not self.registry_file.exists():
            return
        try:
            with open(self.registry_file, "r", encoding="utf-8") as f:
                data = json.load(f)
            self.story_url = data.get("storyUrl", self.story_url)
            self.pattern = data.get("pattern")
            self.pattern_status = data.get("patternStatus", "PENDING")
            self.confidence = data.get("confidence", "LOW")
            self.highest_chapter = data.get("highestChapter", 0)
            self.lowest_chapter = data.get("lowestChapter", 0)
            self.chapters = data.get("chapters", [])
            self.missing_chapters = data.get("missingChapters", [])
            self.discovery_methods = data.get("discoveryMethods", [])
            logger.info(f"Loaded ChapterRegistry with {len(self.chapters)} chapters")
        except Exception as e:
            logger.error(f"Failed to load ChapterRegistry: {e}")
