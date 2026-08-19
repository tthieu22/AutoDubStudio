import os
import shutil
import tempfile
import unittest
import wave
from pathlib import Path
from unittest.mock import patch, MagicMock

from autodub.models.project import Project
from autodub.modules.render_config import RenderConfig
from autodub.modules.mixer import (
    AudioMixer,
    validate_audio_timeline,
    build_audio_filter_graph,
)
from autodub.exceptions import (
    AudioMixError,
    AudioValidationError,
    RenderValidationError,
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


class TestPhase8Mixer(unittest.TestCase):

    def setUp(self):
        self.temp_dir = tempfile.mkdtemp(prefix="autodub_test_mixer_")
        self.project_dir = Path(self.temp_dir) / "test_project"
        self.project = Project(self.project_dir, name="Test Mixer")

        self.project.data["segments"] = [
            {
                "id": 1,
                "start": 0.0,
                "end": 2.5,
                "sync": {"status": "COMPLETED", "path": "audio/synced/000001.wav"}
            },
            {
                "id": 2,
                "start": 3.0,
                "end": 5.0,
                "sync": {"status": "COMPLETED", "path": "audio/synced/000002.wav"}
            }
        ]
        self.project.save()

        synced_dir = self.project_dir / "audio" / "synced"
        create_synthetic_wav(synced_dir / "000001.wav", 2.5)
        create_synthetic_wav(synced_dir / "000002.wav", 2.0)
        create_synthetic_wav(synced_dir / "combined.wav", 5.0)

        # Create dummy source video file
        src_video = self.project_dir / "source" / "input.mp4"
        src_video.parent.mkdir(parents=True, exist_ok=True)
        with open(src_video, "wb") as f:
            f.write(b"MOCK_VIDEO_DATA")

    def tearDown(self):
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_01_dub_only_filter_graph(self):
        fg = build_audio_filter_graph("DUB_ONLY", tts_volume=1.0)
        self.assertIn("volume=1.00", fg)
        self.assertIn("[1:a]", fg)

    def test_02_original_only_filter_graph(self):
        fg = build_audio_filter_graph("ORIGINAL_ONLY", original_volume=0.5)
        self.assertIn("volume=0.50", fg)
        self.assertIn("[0:a]", fg)

    def test_03_mix_filter_graph(self):
        fg = build_audio_filter_graph("MIX", tts_volume=1.0, original_volume=0.3)
        self.assertIn("amix=inputs=2", fg)
        self.assertIn("volume=0.30", fg)

    def test_04_duck_original_filter_graph(self):
        fg = build_audio_filter_graph("DUCK_ORIGINAL", tts_volume=1.0, original_volume=0.15)
        self.assertIn("sidechaincompress", fg)
        self.assertIn("amix=inputs=2", fg)

    def test_05_tts_volume_validation(self):
        cfg = RenderConfig(tts_volume=1.5)
        self.assertEqual(cfg.tts_volume, 1.5)
        with self.assertRaises(RenderValidationError):
            RenderConfig(tts_volume=3.0).validate()

    def test_06_original_volume_validation(self):
        cfg = RenderConfig(original_volume=0.2)
        self.assertEqual(cfg.original_volume, 0.2)
        with self.assertRaises(RenderValidationError):
            RenderConfig(original_volume=-0.1).validate()

    def test_07_invalid_volume(self):
        with self.assertRaises(RenderValidationError):
            RenderConfig(tts_volume=-1.0).validate()

    def test_08_missing_tts_audio(self):
        (self.project_dir / "audio" / "synced" / "000001.wav").unlink()
        with self.assertRaises(AudioValidationError):
            validate_audio_timeline(self.project)

    def test_09_invalid_wav(self):
        corrupt_file = self.project_dir / "audio" / "synced" / "000001.wav"
        with open(corrupt_file, "wb") as f:
            f.write(b"CORRUPTED_DATA")

        with self.assertRaises(AudioValidationError):
            validate_audio_timeline(self.project)

    def test_10_audio_duration_validation(self):
        empty_file = self.project_dir / "audio" / "synced" / "000001.wav"
        with wave.open(str(empty_file), "wb") as wf:
            wf.setnchannels(1)
            wf.setsampwidth(2)
            wf.setframerate(16000)
            wf.writeframes(b"")

        with self.assertRaises(AudioValidationError):
            validate_audio_timeline(self.project)

    def test_11_sample_rate_validation(self):
        validate_audio_timeline(self.project)
        self.assertTrue((self.project_dir / "audio" / "synced" / "combined.wav").exists())

    def test_12_channel_validation(self):
        # Create stereo file
        stereo_file = self.project_dir / "audio" / "synced" / "000001.wav"
        create_synthetic_wav(stereo_file, 2.5, channels=2)
        validate_audio_timeline(self.project)
