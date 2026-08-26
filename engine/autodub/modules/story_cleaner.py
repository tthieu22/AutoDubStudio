import re
from pathlib import Path
from typing import Dict, Any, Optional
from autodub.models.project import Project

class StoryCleaner:
    GUTENBERG_START_MARKERS = [
        r"\*\*\*\s*START OF TH(IS|E) PROJECT GUTENBERG EBOOK.*?\*\*\*",
        r"\*\*\*\s*START OF THE GUTENBERG EBOOK.*?\*\*\*",
        r"START OF THIS PROJECT GUTENBERG EBOOK"
    ]
    GUTENBERG_END_MARKERS = [
        r"\*\*\*\s*END OF TH(IS|E) PROJECT GUTENBERG EBOOK.*?\*\*\*",
        r"\*\*\*\s*END OF THE GUTENBERG EBOOK.*?\*\*\*",
        r"End of Project Gutenberg's",
        r"End of the Project Gutenberg"
    ]

    @staticmethod
    def clean_gutenberg_text(text: str) -> str:
        cleaned = text
        # Strip Start Header
        for marker in StoryCleaner.GUTENBERG_START_MARKERS:
            match = re.search(marker, cleaned, flags=re.IGNORECASE | re.DOTALL)
            if match:
                cleaned = cleaned[match.end():]
                break

        # Strip End Footer
        for marker in StoryCleaner.GUTENBERG_END_MARKERS:
            match = re.search(marker, cleaned, flags=re.IGNORECASE | re.DOTALL)
            if match:
                cleaned = cleaned[:match.start()]
                break

        return cleaned

    @staticmethod
    def clean_wikitext(text: str) -> str:
        cleaned = text
        # Remove file/image tags [[File:...]] [[Tập tin:...]] [[Image:...]]
        cleaned = re.sub(r"\[\[(File|Tập tin|Image|Hình):.*?\]\]", "", cleaned, flags=re.IGNORECASE | re.DOTALL)
        # Remove categories [[Category:...]] [[Thể loại:...]]
        cleaned = re.sub(r"\[\[(Category|Thể loại):.*?\]\]", "", cleaned, flags=re.IGNORECASE | re.DOTALL)
        # Convert wikilinks [[link|text]] -> text, [[link]] -> link
        cleaned = re.sub(r"\[\[(?:[^|\]]*\|)?([^\]]+)\]\]", r"\1", cleaned)
        # Remove templates {{...}}
        cleaned = re.sub(r"\{\{.*?\}\}", "", cleaned, flags=re.DOTALL)
        # Convert headers == Header == -> Header
        cleaned = re.sub(r"={2,6}\s*(.*?)\s*={2,6}", r"\1", cleaned)
        # Remove HTML tags <...>
        cleaned = re.sub(r"<[^>]+>", "", cleaned)
        return cleaned

    @staticmethod
    def sanitize_whitespace(text: str) -> str:
        # Normalize line endings
        lines = [line.strip() for line in text.splitlines()]
        # Remove duplicate consecutive blank lines
        result_lines = []
        blank = False
        for line in lines:
            if not line:
                if not blank:
                    result_lines.append("")
                    blank = True
            else:
                result_lines.append(line)
                blank = False
        return "\n".join(result_lines).strip()

    def clean_project_story(self, project: Project) -> str:
        project_dir = project.project_dir
        original_file = project_dir / "story" / "original.txt"
        if not original_file.exists():
            raise FileNotFoundError(f"Original story file not found: {original_file}")

        raw_text = original_file.read_text(encoding="utf-8")
        source_meta = project.data.get("story", {})
        source_type = source_meta.get("source_type", "general")

        if source_type == "gutenberg":
            text = self.clean_gutenberg_text(raw_text)
        elif source_type == "wikisource":
            text = self.clean_wikitext(raw_text)
        else:
            text = self.clean_gutenberg_text(raw_text)
            text = self.clean_wikitext(text)

        cleaned_text = self.sanitize_whitespace(text)

        cleaned_file = project_dir / "story" / "cleaned.txt"
        with open(cleaned_file, "w", encoding="utf-8") as f:
            f.write(cleaned_text)

        # Update Project Meta
        project.data["story"]["status"] = "CLEANED"
        project.save()

        return cleaned_text
