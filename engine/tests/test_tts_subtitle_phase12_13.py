import json
import shutil
import tempfile
import unittest
from pathlib import Path

from autodub.models.project import Project
from autodub.modules.piper_story_tts import StoryTTSEngine
from autodub.modules.subtitle_engine import SubtitleEngine, format_ass_timestamp

class TestPhase1213TTSSubtitles(unittest.TestCase):
    def setUp(self):
        self.test_dir = Path(tempfile.mkdtemp(prefix="autodub_p12_test_"))
        self.project_dir = self.test_dir / "tts_sub_proj"
        self.project = Project(self.project_dir, name="tts_sub_test", mode="MODE_STORY")
        
        self.scenes = [
            {
                "id": "scene_001",
                "chapter_index": 1,
                "scene_index": 1,
                "speaker": "NARRATOR",
                "narration": "Đêm đó mưa rất to.",
                "duration": 4.0
            },
            {
                "id": "scene_002",
                "chapter_index": 1,
                "scene_index": 2,
                "speaker": "A_LANG",
                "narration": "Ai đứng ngoài đó vậy?",
                "duration": 3.0
            }
        ]

    def tearDown(self):
        if self.test_dir.exists():
            shutil.rmtree(self.test_dir, ignore_errors=True)

    def test_01_story_tts_audio_generation(self):
        tts_engine = StoryTTSEngine(self.project)
        wav_path = tts_engine.generate_audio_for_scene(self.scenes[0])
        
        self.assertTrue(wav_path.exists())
        self.assertEqual(wav_path.name, "scene_001.wav")
        self.assertEqual(self.scenes[0]["audio_path"], "assets/audio/scene_001.wav")
        self.assertGreater(self.scenes[0]["audio_duration"], 0)

    def test_02_subtitle_generation_srt_and_ass(self):
        sub_engine = SubtitleEngine(self.project)
        files = sub_engine.generate_subtitles(self.scenes)

        self.assertTrue(files["srt"].exists())
        self.assertTrue(files["ass"].exists())

        srt_content = files["srt"].read_text(encoding="utf-8")
        self.assertIn("Đêm đó mưa rất to.", srt_content)
        self.assertIn("[A_LANG] Ai đứng ngoài đó vậy?", srt_content)

        ass_content = files["ass"].read_text(encoding="utf-8")
        self.assertIn("Style: Narrator", ass_content)
        self.assertIn("Style: Character", ass_content)
        self.assertIn("Dialogue: 0,", ass_content)

    def test_03_format_ass_timestamp(self):
        self.assertEqual(format_ass_timestamp(0.0), "0:00:00.00")
        self.assertEqual(format_ass_timestamp(65.45), "0:01:05.45")

if __name__ == "__main__":
    unittest.main()
