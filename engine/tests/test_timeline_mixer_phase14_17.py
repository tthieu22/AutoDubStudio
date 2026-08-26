import json
import shutil
import tempfile
import unittest
from pathlib import Path

from autodub.models.project import Project
from autodub.modules.timeline_engine import TimelineEngine
from autodub.modules.text_overlay import TextOverlayEngine
from autodub.modules.audio_mixer_engine import AudioMixerEngine

class TestPhase14To17TimelineMixer(unittest.TestCase):
    def setUp(self):
        self.test_dir = Path(tempfile.mkdtemp(prefix="autodub_p14_test_"))
        self.project_dir = self.test_dir / "timeline_proj"
        self.project = Project(self.project_dir, name="timeline_test", mode="MODE_STORY")
        
        self.scenes = [
            {
                "id": "scene_001",
                "chapter_index": 1,
                "speaker": "NARRATOR",
                "narration": "Đêm đó mưa rất to.",
                "duration": 5.0,
                "image_path": "assets/images/scene_001.png",
                "audio_path": "assets/audio/scene_001.wav"
            },
            {
                "id": "scene_002",
                "chapter_index": 1,
                "speaker": "A_LANG",
                "narration": "Ai đứng ở ngoài kia?",
                "duration": 4.0,
                "image_path": "assets/images/scene_002.png",
                "audio_path": "assets/audio/scene_002.wav"
            }
        ]

    def tearDown(self):
        if self.test_dir.exists():
            shutil.rmtree(self.test_dir, ignore_errors=True)

    def test_01_timeline_building(self):
        te = TimelineEngine(self.project)
        tl = te.build_timeline(self.scenes)

        self.assertEqual(tl["total_duration"], 9.0)
        self.assertEqual(len(tl["tracks"]), 6)
        self.assertTrue((self.project_dir / "timeline" / "timeline.json").exists())

    def test_02_text_overlay_filter_building(self):
        overlay = TextOverlayEngine(self.project)
        filter_str = overlay.build_chapter_title_filter("TẬP 01: ĐÊM MƯA", duration_sec=3.0)

        self.assertIn("drawtext", filter_str)
        self.assertIn("TẬP 01", filter_str)
        self.assertIn("between(t,0,3.00)", filter_str)

    def test_03_audio_mixing(self):
        te = TimelineEngine(self.project)
        tl = te.build_timeline(self.scenes)

        mixer = AudioMixerEngine(self.project)
        mixed_wav = mixer.mix_audio_tracks(tl)

        self.assertTrue(mixed_wav.exists())
        self.assertEqual(mixed_wav.name, "mixed_master.wav")

if __name__ == "__main__":
    unittest.main()
