import json
import os
import shutil
import tempfile
import unittest
import wave
from pathlib import Path
from unittest.mock import patch, MagicMock

from autodub.models.project import Project
from autodub.pipeline.manager import PipelineManager
from autodub.pipeline.state import PipelineStage, StageStatus
from autodub.modules.render_config import RenderConfig
from autodub.modules.renderer import RealRenderer, VideoRenderer
from autodub.exceptions import PipelineCancelledError, RenderCancelledError
from tests.test_translator_phase5 import MockOllamaClient
from tests.test_tts_phase6 import MockPiperClient


def create_synthetic_wav(path: Path, duration: float, sample_rate: int = 16000, channels: int = 1):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    num_frames = int(max(0.01, duration) * sample_rate)
    frame_data = b"\x10\x00" * channels

    with wave.open(str(path), "wb") as wf:
        wf.setnchannels(channels)
        wf.setsampwidth(2)
        wf.setframerate(sample_rate)
        wf.writeframes(frame_data * num_frames)


def create_sample_srt(path: Path):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    content = (
        "1\n"
        "00:00:00,000 --> 00:00:02,500\n"
        "Xin chào thế giới\n\n"
        "2\n"
        "00:00:03,000 --> 00:00:05,000\n"
        "Chào buổi sáng\n"
    )
    with open(path, "w", encoding="utf-8") as f:
        f.write(content)


class TestPhase8RenderIntegration(unittest.TestCase):

    def setUp(self):
        self.temp_dir = tempfile.mkdtemp(prefix="autodub_test_render_int_")
        self.project_dir = Path(self.temp_dir) / "test_project"
        self.project = Project(self.project_dir, name="Integration Test Project")

        self.project.data["segments"] = [
            {"id": 1, "start": 0.0, "end": 2.5, "text": "Hello", "translated_text": "Xin chào", "sync": {"status": "COMPLETED", "path": "audio/synced/000001.wav"}},
            {"id": 2, "start": 3.0, "end": 5.0, "text": "Morning", "translated_text": "Chào buổi sáng", "sync": {"status": "COMPLETED", "path": "audio/synced/000002.wav"}}
        ]
        for stage in ["extract", "transcribe", "translate", "tts", "sync"]:
            self.project.update_stage(stage, StageStatus.COMPLETED.value, progress=100)

        self.project.save()

        synced_dir = self.project_dir / "audio" / "synced"
        create_synthetic_wav(synced_dir / "000001.wav", 2.5)
        create_synthetic_wav(synced_dir / "000002.wav", 2.0)
        create_synthetic_wav(synced_dir / "combined.wav", 5.0)

        create_sample_srt(self.project_dir / "transcript" / "translated.srt")

        src_video = self.project_dir / "source" / "input.mp4"
        src_video.parent.mkdir(parents=True, exist_ok=True)
        with open(src_video, "wb") as f:
            f.write(b"MOCK_VIDEO_DATA")

    def tearDown(self):
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def _mock_successful_render(self, renderer):
        def mock_mix(*args, **kwargs):
            return self.project_dir / "audio" / "mixed_audio.wav"

        def mock_exec(*args, **kwargs):
            out_file = self.project_dir / "output" / ".final.mp4.tmp"
            with open(out_file, "wb") as f:
                f.write(b"MOCK_MP4_DATA")

        mock_probe = {
            "format": {"duration": "5.0"},
            "streams": [{"codec_type": "video", "width": 1920, "height": 1080, "r_frame_rate": "30/1"}]
        }

        p1 = patch.object(renderer.mixer, "mix_project_audio", side_effect=mock_mix)
        p2 = patch.object(renderer, "_execute_ffmpeg_with_progress", side_effect=mock_exec)
        p3 = patch("autodub.modules.renderer.validate_rendered_output", return_value=mock_probe)
        p4 = patch.object(renderer.runner, "probe", return_value=mock_probe)
        return p1, p2, p3, p4

    def test_01_end_to_end_render_pipeline(self):
        renderer = RealRenderer(step_delay=0.01)
        p1, p2, p3, p4 = self._mock_successful_render(renderer)
        with p1, p2, p3, p4:
            t = renderer.run(self.project)
            self.assertEqual(self.project.get_stage_info("render")["status"], StageStatus.COMPLETED.value)
            self.assertTrue((self.project_dir / "output" / "final.mp4").exists())

    def test_02_dub_only_mode(self):
        cfg = RenderConfig(audio_mode="DUB_ONLY")
        renderer = RealRenderer(step_delay=0.01)
        p1, p2, p3, p4 = self._mock_successful_render(renderer)
        with p1, p2, p3, p4:
            t = renderer.run(self.project, render_config=cfg)
            self.assertEqual(self.project.data["render"]["audio_mode"], "DUB_ONLY")

    def test_03_mix_mode(self):
        cfg = RenderConfig(audio_mode="MIX", original_volume=0.3)
        renderer = RealRenderer(step_delay=0.01)
        p1, p2, p3, p4 = self._mock_successful_render(renderer)
        with p1, p2, p3, p4:
            t = renderer.run(self.project, render_config=cfg)
            self.assertEqual(self.project.data["render"]["audio_mode"], "MIX")

    def test_04_duck_original_mode(self):
        cfg = RenderConfig(audio_mode="DUCK_ORIGINAL")
        renderer = RealRenderer(step_delay=0.01)
        p1, p2, p3, p4 = self._mock_successful_render(renderer)
        with p1, p2, p3, p4:
            t = renderer.run(self.project, render_config=cfg)
            self.assertEqual(self.project.data["render"]["audio_mode"], "DUCK_ORIGINAL")

    def test_05_h264_cpu_render(self):
        cfg = RenderConfig(video_codec="H264", encoder="CPU")
        renderer = RealRenderer(step_delay=0.01)
        p1, p2, p3, p4 = self._mock_successful_render(renderer)
        with p1, p2, p3, p4:
            t = renderer.run(self.project, render_config=cfg)
            self.assertEqual(self.project.data["render"]["video_codec"], "H264")

    def test_06_h265_cpu_render(self):
        cfg = RenderConfig(video_codec="H265", encoder="CPU")
        renderer = RealRenderer(step_delay=0.01)
        p1, p2, p3, p4 = self._mock_successful_render(renderer)
        with p1, p2, p3, p4:
            t = renderer.run(self.project, render_config=cfg)
            self.assertEqual(self.project.data["render"]["video_codec"], "H265")

    def test_07_nvenc_render(self):
        cfg = RenderConfig(video_codec="H264", encoder="NVENC")
        renderer = RealRenderer(step_delay=0.01)
        p1, p2, p3, p4 = self._mock_successful_render(renderer)
        with p1, p2, p3, p4, patch("autodub.modules.renderer.detect_available_encoders", return_value={"h264_nvenc": True}):
            t = renderer.run(self.project, render_config=cfg)
            self.assertEqual(self.project.data["render"]["encoder"], "h264_nvenc")

    def test_08_subtitle_copy(self):
        cfg = RenderConfig(subtitle_mode="COPY")
        renderer = RealRenderer(step_delay=0.01)
        p1, p2, p3, p4 = self._mock_successful_render(renderer)
        with p1, p2, p3, p4:
            t = renderer.run(self.project, render_config=cfg)
            self.assertEqual(self.project.data["render"]["subtitle_mode"], "COPY")

    def test_09_subtitle_burn_in(self):
        cfg = RenderConfig(subtitle_mode="BURN_IN")
        renderer = RealRenderer(step_delay=0.01)
        p1, p2, p3, p4 = self._mock_successful_render(renderer)
        with p1, p2, p3, p4:
            t = renderer.run(self.project, render_config=cfg)
            self.assertEqual(self.project.data["render"]["subtitle_mode"], "BURN_IN")

    def test_10_no_subtitle(self):
        cfg = RenderConfig(subtitle_mode="NONE")
        renderer = RealRenderer(step_delay=0.01)
        p1, p2, p3, p4 = self._mock_successful_render(renderer)
        with p1, p2, p3, p4:
            t = renderer.run(self.project, render_config=cfg)
            self.assertEqual(self.project.data["render"]["subtitle_mode"], "NONE")

    def test_11_render_cancellation(self):
        renderer = RealRenderer(step_delay=0.01)
        with self.assertRaises(PipelineCancelledError):
            renderer.run(self.project, is_cancelled=lambda: True)
        self.assertEqual(self.project.get_stage_info("render")["status"], StageStatus.CANCELLED.value)

    def test_12_interrupted_render_recovery(self):
        chk_file = self.project_dir / "output" / "render.partial.json"
        chk_file.parent.mkdir(parents=True, exist_ok=True)
        with open(chk_file, "w", encoding="utf-8") as f:
            json.dump({"status": "RUNNING", "config_hash": "OLD_HASH"}, f)

        renderer = RealRenderer(step_delay=0.01)
        p1, p2, p3, p4 = self._mock_successful_render(renderer)
        with p1, p2, p3, p4:
            t = renderer.run(self.project)
            self.assertEqual(self.project.get_stage_info("render")["status"], StageStatus.COMPLETED.value)

    def test_13_existing_valid_output_skip(self):
        renderer = RealRenderer(step_delay=0.01)
        p1, p2, p3, p4 = self._mock_successful_render(renderer)
        with p1, p2, p3, p4:
            renderer.run(self.project)
            # Second run without force should skip
            t2 = renderer.run(self.project)
            self.assertEqual(t2, 0.0)

    def test_14_corrupted_output_regeneration(self):
        out_file = self.project_dir / "output" / "final.mp4"
        out_file.parent.mkdir(parents=True, exist_ok=True)
        with open(out_file, "wb") as f:
            f.write(b"CORRUPTED_DATA")

        renderer = RealRenderer(step_delay=0.01)
        p1, p2, p3, p4 = self._mock_successful_render(renderer)
        with p1, p2, p3, p4:
            renderer.run(self.project)
            self.assertEqual(self.project.get_stage_info("render")["status"], StageStatus.COMPLETED.value)

    def test_15_video_renderer_public_api(self):
        api = VideoRenderer(step_delay=0.01)
        renderer = RealRenderer(step_delay=0.01)
        p1, p2, p3, p4 = self._mock_successful_render(renderer)
        with p1, p2, p3, p4, patch("autodub.modules.renderer.RealRenderer", return_value=renderer):
            res = api.render_project(self.project_dir, force=True)
            self.assertTrue(res.output_path.exists())
            self.assertGreater(res.duration, 0.0)
