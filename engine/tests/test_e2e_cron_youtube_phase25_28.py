import json
import shutil
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch, MagicMock

from autodub.models.project import Project
from autodub.modules.story_collector import StoryCollector
from autodub.modules.story_cleaner import StoryCleaner
from autodub.modules.story_analyzer import StoryAnalyzer
from autodub.modules.scene_planner import ScenePlanner
from autodub.modules.sd_image_generator import SDImageGenerator
from autodub.modules.piper_story_tts import StoryTTSEngine
from autodub.modules.subtitle_engine import SubtitleEngine
from autodub.modules.timeline_engine import TimelineEngine
from autodub.modules.audio_mixer_engine import AudioMixerEngine
from autodub.modules.story_renderer import StoryRenderer
from autodub.modules.final_qa import FinalQAChecker
from autodub.modules.youtube_publisher import YouTubePublisher

class TestPhase25To28E2E(unittest.TestCase):
    def setUp(self):
        self.test_dir = Path(tempfile.mkdtemp(prefix="autodub_e2e_test_"))
        self.project_dir = self.test_dir / "e2e_story_proj"
        self.project = Project(self.project_dir, name="e2e_story_test", mode="MODE_STORY")
        from autodub.utils.files import ensure_project_structure
        ensure_project_structure(self.project_dir)

    def tearDown(self):
        if self.test_dir.exists():
            shutil.rmtree(self.test_dir, ignore_errors=True)

    def test_01_full_end_to_end_story_pipeline(self):
        # 1. Setup original text
        raw_text = "*** START OF EBOOK ***\nChương 1: Đêm Mưa Ở Làng Cổ\nA Lăng mang chiếc đèn lồng đỏ bước ra cổng làng.\nMẫu Đơn đứng đó lặng lẽ."
        (self.project_dir / "story" / "original.txt").write_text(raw_text, encoding="utf-8")
        self.project.data["story"] = {"source_type": "gutenberg", "title": "Đêm Mưa", "status": "FETCHED"}

        # 2. Clean
        cleaner = StoryCleaner()
        cleaner.clean_project_story(self.project)
        self.assertEqual(self.project.data["story"]["status"], "CLEANED")

        # 3. Analyze
        analyzer = StoryAnalyzer()
        analyzer.analyze_project_story(self.project)
        self.assertEqual(self.project.data["story"]["status"], "ANALYZED")

        # 4. Plan Scenes
        planner = ScenePlanner()
        scenes = planner.plan_chapter_scenes(self.project, chapter_index=1)
        self.assertGreater(len(scenes), 0)

        # 5. Generate Images
        img_gen = SDImageGenerator(self.project)
        for sc in scenes:
            img_gen.generate_image_for_scene(sc, bypass_review=True)

        # 6. Generate Audio
        tts_engine = StoryTTSEngine(self.project)
        for sc in scenes:
            tts_engine.generate_audio_for_scene(sc)

        # 7. Subtitles
        sub_engine = SubtitleEngine(self.project)
        sub_engine.generate_subtitles(scenes)

        # 8. Timeline
        te = TimelineEngine(self.project)
        tl = te.build_timeline(scenes)

        # 9. Mix Audio
        mixer = AudioMixerEngine(self.project)
        mixer.mix_audio_tracks(tl)

        # 10. Render Final
        renderer = StoryRenderer(self.project)
        final_mp4 = renderer.render_final(self.project)
        self.assertTrue(final_mp4.exists())
        self.assertEqual(self.project.data["story"]["status"], "RENDERED")

        # 11. Final QA
        qa = FinalQAChecker(self.project)
        qa_report = qa.run_qa()
        self.assertEqual(qa_report["overall_status"], "PASS")

        # 12. YouTube Publisher
        pub = YouTubePublisher(self.project)
        res = pub.publish_video(privacy_status="private")
        self.assertIn("video_id", res)
        self.assertEqual(self.project.data["story"]["status"], "PUBLISHED")

if __name__ == "__main__":
    unittest.main()
