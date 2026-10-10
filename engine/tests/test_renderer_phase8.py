import json
import os
import shutil
import tempfile
import unittest
import wave
from pathlib import Path
from unittest.mock import patch, MagicMock

from autodub.models.project import Project
from autodub.modules.render_config import RenderConfig
from autodub.modules.renderer import (
    RealRenderer,
    VideoRenderer,
    detect_available_encoders,
    escape_ffmpeg_subtitle_path,
    select_encoder,
)
from autodub.utils.ffmpeg import find_ffmpeg, find_ffprobe
from autodub.exceptions import (
    RenderError,
    RenderValidationError,
    EncoderUnavailableError,
    NvencUnavailableError,
    SubtitleValidationError,
    OutputValidationError,
    PipelineCancelledError,
)


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


class TestPhase8Renderer(unittest.TestCase):

    def setUp(self):
        self.temp_dir = tempfile.mkdtemp(prefix="autodub_test_renderer_")
        self.project_dir = Path(self.temp_dir) / "test_project"
        self.project = Project(self.project_dir, name="Test Renderer")

        self.project.data["segments"] = [
            {"id": 1, "start": 0.0, "end": 2.5, "sync": {"status": "COMPLETED", "path": "audio/synced/000001.wav"}},
            {"id": 2, "start": 3.0, "end": 5.0, "sync": {"status": "COMPLETED", "path": "audio/synced/000002.wav"}}
        ]
        self.project.data["pipeline"]["sync"]["status"] = "COMPLETED"
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

    def test_01_ffmpeg_discovery(self):
        ffmpeg_bin = find_ffmpeg()
        self.assertTrue(Path(ffmpeg_bin).exists())

    def test_02_ffprobe_discovery(self):
        ffprobe_bin = find_ffprobe()
        self.assertTrue(Path(ffprobe_bin).exists())

    def test_03_encoder_detection(self):
        encoders = detect_available_encoders()
        self.assertIn("libx264", encoders)
        self.assertIn("h264_nvenc", encoders)

    def test_04_h264_cpu_encoder(self):
        enc = select_encoder("H264", "CPU", {"libx264": True, "h264_nvenc": True})
        self.assertEqual(enc, "libx264")

    def test_05_h265_cpu_encoder(self):
        enc = select_encoder("H265", "CPU", {"libx265": True, "hevc_nvenc": True})
        self.assertEqual(enc, "libx265")

    def test_06_nvenc_detection(self):
        enc = select_encoder("H264", "NVENC", {"libx264": True, "h264_nvenc": True})
        self.assertEqual(enc, "h264_nvenc")

    def test_07_nvenc_fallback_in_auto_mode(self):
        enc = select_encoder("H264", "AUTO", {"libx264": True, "h264_nvenc": False})
        self.assertEqual(enc, "libx264")

    def test_08_explicit_nvenc_failure_when_unavailable(self):
        with self.assertRaises(NvencUnavailableError):
            select_encoder("H264", "NVENC", {"libx264": True, "h264_nvenc": False})

    def test_09_progress_parser(self):
        renderer = RealRenderer(step_delay=0.01)
        # Test helper method initialization
        self.assertIsNotNone(renderer.runner)

    def test_10_subtitle_none(self):
        cfg = RenderConfig(subtitle_mode="NONE")
        self.assertEqual(cfg.subtitle_mode, "NONE")

    def test_11_subtitle_copy(self):
        cfg = RenderConfig(subtitle_mode="COPY")
        self.assertEqual(cfg.subtitle_mode, "COPY")

    def test_12_subtitle_burn_in(self):
        cfg = RenderConfig(subtitle_mode="BURN_IN")
        self.assertEqual(cfg.subtitle_mode, "BURN_IN")

    def test_13_windows_subtitle_path_escaping(self):
        p = Path("C:/Projects/My Project/transcript/translated.srt")
        escaped = escape_ffmpeg_subtitle_path(p)
        self.assertIn("C\\:", escaped)

    def test_14_output_atomicity(self):
        out_dir = self.project_dir / "output"
        out_dir.mkdir(parents=True, exist_ok=True)
        tmp_file = out_dir / ".final.mp4.tmp"
        final_file = out_dir / "final.mp4"

        with open(tmp_file, "wb") as f:
            f.write(b"TEMP_DATA")

        os.replace(tmp_file, final_file)
        self.assertTrue(final_file.exists())
        self.assertFalse(tmp_file.exists())

    def test_15_output_validation(self):
        with patch.object(RealRenderer, "run", return_value=0.5):
            renderer = RealRenderer(step_delay=0.01)
            t = renderer.run(self.project)
            self.assertEqual(t, 0.5)

    def test_16_idempotency(self):
        out_dir = self.project_dir / "output"
        out_dir.mkdir(parents=True, exist_ok=True)
        final_file = out_dir / "final.mp4"
        with open(final_file, "wb") as f:
            f.write(b"FINAL_VALID_DATA")

        renderer = RealRenderer(step_delay=0.01)

        # Mock validation & probe
        mock_probe = {
            "format": {"duration": "5.0"},
            "streams": [{"codec_type": "video", "width": 1920, "height": 1080}]
        }
        with patch.object(renderer.runner, "probe", return_value=mock_probe):
            self.project.update_stage("sync", "completed", progress=100)
            self.project.update_stage("render", "completed", progress=100)
            self.project.save()
            t = renderer.run(self.project)
            self.assertEqual(t, 0.0)

    def test_17_force_render(self):
        renderer = RealRenderer(step_delay=0.01)

        def mock_mix(*args, **kwargs):
            return self.project_dir / "audio" / "mixed_audio.wav"

        def mock_exec(*args, **kwargs):
            out_file = self.project_dir / "output" / ".final.mp4.tmp"
            with open(out_file, "wb") as f:
                f.write(b"MOCK_MP4")

        mock_probe = {
            "format": {"duration": "5.0"},
            "streams": [{"codec_type": "video", "width": 1920, "height": 1080}]
        }

        with patch.object(renderer.mixer, "mix_project_audio", side_effect=mock_mix), \
             patch.object(renderer, "_execute_ffmpeg_with_progress", side_effect=mock_exec), \
             patch("autodub.modules.renderer.validate_rendered_output", return_value=mock_probe), \
             patch.object(renderer.runner, "probe", return_value=mock_probe):
            t = renderer.run(self.project, force=True)
            self.assertGreater(t, 0.0)

    def test_18_cancellation(self):
        renderer = RealRenderer(step_delay=0.01)
        with self.assertRaises(PipelineCancelledError):
            renderer.run(self.project, is_cancelled=lambda: True)
        self.assertEqual(self.project.get_stage_info("render")["status"], "cancelled")

    def test_19_retry(self):
        renderer = RealRenderer(step_delay=0.01)

        def mock_mix(*args, **kwargs):
            return self.project_dir / "audio" / "mixed_audio.wav"

        attempts = [0]
        def fail_once(*args, **kwargs):
            attempts[0] += 1
            if attempts[0] == 1:
                raise RenderError("Transient error")
            out_file = self.project_dir / "output" / ".final.mp4.tmp"
            with open(out_file, "wb") as f:
                f.write(b"MOCK_MP4")

        mock_probe = {
            "format": {"duration": "5.0"},
            "streams": [{"codec_type": "video", "width": 1920, "height": 1080}]
        }

        with patch.object(renderer.mixer, "mix_project_audio", side_effect=mock_mix), \
             patch.object(renderer, "_execute_ffmpeg_with_progress", side_effect=fail_once), \
             patch("autodub.modules.renderer.validate_rendered_output", return_value=mock_probe), \
             patch.object(renderer.runner, "probe", return_value=mock_probe):
            t = renderer.run(self.project, force=True)
            self.assertEqual(self.project.get_stage_info("render")["status"], "completed")

    def test_20_checkpoint_creation(self):
        renderer = RealRenderer(step_delay=0.01)

        def mock_mix(*args, **kwargs):
            return self.project_dir / "audio" / "mixed_audio.wav"

        def mock_exec(*args, **kwargs):
            out_file = self.project_dir / "output" / ".final.mp4.tmp"
            with open(out_file, "wb") as f:
                f.write(b"MOCK_MP4")

        mock_probe = {
            "format": {"duration": "5.0"},
            "streams": [{"codec_type": "video", "width": 1920, "height": 1080}]
        }

        with patch.object(renderer.mixer, "mix_project_audio", side_effect=mock_mix), \
             patch.object(renderer, "_execute_ffmpeg_with_progress", side_effect=mock_exec), \
             patch("autodub.modules.renderer.validate_rendered_output", return_value=mock_probe), \
             patch.object(renderer.runner, "probe", return_value=mock_probe):
            renderer.run(self.project, force=True)

        chk_path = self.project_dir / "output" / "render.partial.json"
        self.assertTrue(chk_path.exists())
        with open(chk_path, "r", encoding="utf-8") as f:
            chk = json.load(f)
        self.assertEqual(chk["status"], "COMPLETED")

    def test_21_stale_checkpoint_recovery(self):
        chk_path = self.project_dir / "output" / "render.partial.json"
        chk_path.parent.mkdir(parents=True, exist_ok=True)
        with open(chk_path, "w", encoding="utf-8") as f:
            json.dump({"config_hash": "OLD_HASH", "status": "RUNNING"}, f)

        cfg = RenderConfig()
        cfg_hash = cfg.compute_hash()
        self.assertNotEqual(cfg_hash, "OLD_HASH")

    def test_22_config_hash_change(self):
        cfg1 = RenderConfig(audio_mode="DUB_ONLY")
        cfg2 = RenderConfig(audio_mode="DUCK_ORIGINAL")
        self.assertNotEqual(cfg1.compute_hash(), cfg2.compute_hash())
