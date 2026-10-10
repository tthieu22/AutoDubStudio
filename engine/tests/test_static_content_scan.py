import os
import re
import unittest
from pathlib import Path


class TestStaticContentScan(unittest.TestCase):
    """
    Scans production generation files (novel_engine.py, story_director.py, master_planner.py, cli.py)
    to ensure ZERO hardcoded Xianxia story strings exist in production generation or fallback logic.
    """

    FORBIDDEN_KEYWORDS = [
        "Lâm Phàm",
        "Thanh Vân Tông",
        "Thanh Vân Quả",
        "Tiên Giới",
        "Trúc Cơ",
        "Luyện Khí",
        "Vô Địch Tiên Đế",
        "_generate_default_25_arcs"
    ]

    PRODUCTION_FILES = [
        "autodub/novel/novel_engine.py",
        "autodub/novel/prompts/story_director.py",
        "autodub/novel/prompts/master_planner.py",
        "autodub/cli.py"
    ]

    def test_no_forbidden_hardcoded_story_strings_in_production(self):
        engine_root = Path(__file__).parent.parent
        violations = []

        for rel_path in self.PRODUCTION_FILES:
            full_path = engine_root / rel_path
            self.assertTrue(full_path.exists(), f"Production file not found: {full_path}")

            content = full_path.read_text(encoding="utf-8")
            for kw in self.FORBIDDEN_KEYWORDS:
                matches = [m.start() for m in re.finditer(re.escape(kw), content, re.IGNORECASE)]
                if matches:
                    violations.append(f"File '{rel_path}' contains forbidden hardcoded string '{kw}' at {len(matches)} occurrence(s).")

        self.assertEqual(len(violations), 0, f"Static Content Audit Violations Detected:\n" + "\n".join(violations))


if __name__ == "__main__":
    unittest.main()
