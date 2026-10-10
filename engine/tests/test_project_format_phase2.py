import json
import shutil
import tempfile
import unittest
from pathlib import Path

from autodub.models.project import Project
from autodub.utils.files import ensure_project_structure

class TestPhase2ProjectFormat(unittest.TestCase):
    def setUp(self):
        self.test_dir = Path(tempfile.mkdtemp(prefix="autodub_p2_test_"))
        self.project_dir = self.test_dir / "project_001"

    def tearDown(self):
        if self.test_dir.exists():
            shutil.rmtree(self.test_dir, ignore_errors=True)

    def test_01_ensure_project_structure_directories(self):
        ensure_project_structure(self.project_dir)
        required_dirs = [
            "source", "story", "story/chapters", "story/summaries",
            "characters", "scenes", "assets", "assets/images", "assets/video",
            "assets/music", "audio", "audio/tts", "audio/synced",
            "transcript", "timeline", "subtitles", "output", "logs"
        ]
        for rel in required_dirs:
            p = self.project_dir / rel
            self.assertTrue(p.exists() and p.is_dir(), f"Missing directory: {rel}")

    def test_02_create_and_load_dubbing_project(self):
        proj = Project(self.project_dir, name="test_dubbing", source_path="source/video.mp4")
        self.assertEqual(proj.data["mode"], "MODE_DUBBING")
        self.assertEqual(proj.data["version"], 1)
        self.assertTrue((self.project_dir / "project.json").exists())

        # Reload
        reloaded = Project(self.project_dir)
        self.assertEqual(reloaded.data["mode"], "MODE_DUBBING")
        self.assertEqual(reloaded.data["name"], "test_dubbing")

    def test_03_create_and_load_story_project(self):
        proj_dir_story = self.test_dir / "story_project_001"
        proj = Project(proj_dir_story, name="test_story", mode="MODE_STORY")
        self.assertEqual(proj.data["mode"], "MODE_STORY")
        self.assertIn("story", proj.data)
        self.assertIn("characters", proj.data)
        self.assertIn("scenes", proj.data)
        self.assertIn("timeline", proj.data)

        # Reload
        reloaded = Project(proj_dir_story)
        self.assertEqual(reloaded.data["mode"], "MODE_STORY")

    def test_04_save_and_backup_recovery(self):
        proj = Project(self.project_dir, name="test_backup")
        proj.data["story"]["title"] = "Lieu Trai Chi Di"
        proj.save()

        bak_file = self.project_dir / "project.json.bak"
        self.assertTrue(bak_file.exists())

        # Corrupt main file
        with open(self.project_dir / "project.json", "w", encoding="utf-8") as f:
            f.write("{ INVALID JSON ")

        # Load should recover automatically
        recovered = Project(self.project_dir)
        self.assertEqual(recovered.data["story"]["title"], "Lieu Trai Chi Di")

if __name__ == "__main__":
    unittest.main()
