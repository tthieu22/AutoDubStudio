import json
import os
import shutil
import tempfile
import unittest
from pathlib import Path

from autodub.models.project import Project
from autodub.pipeline.state import PipelineStage, StageStatus
from autodub.utils.ffmpeg import find_ffmpeg, FFmpegRunner
from autodub.modules.extractor import RealExtractor
from autodub.modules.transcriber import (
    RealTranscriber, format_srt_timestamp, validate_srt_content
)
from autodub.exceptions import AutoDubError, PipelineCancelledError
from tests.test_extractor_phase3 import create_synthetic_media

class MockWhisperSegment:
    def __init__(self, start: float, end: float, text: str):
        self.start = start
        self.end = end
        self.text = text

class MockWhisperInfo:
    def __init__(self, language: str = "en", language_probability: float = 0.99):
        self.language = language
        self.language_probability = language_probability

class MockWhisperModel:
    def __init__(self, *args, **kwargs):
        pass

    def transcribe(self, audio_path: str, **kwargs):
        info = MockWhisperInfo(language="en", language_probability=0.99)
        segments = [
            MockWhisperSegment(0.5, 3.2, "Hello everyone, welcome to AutoDubStudio."),
            MockWhisperSegment(3.5, 6.8, "This is a local AI video dubbing pipeline.")
        ]
        return iter(segments), info

class TestPhase4Transcriber(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.test_dir = Path(tempfile.mkdtemp(prefix="autodub_p4_"))
        cls.sample_video = cls.test_dir / "sample.mp4"
        create_synthetic_media(cls.sample_video, has_audio=True, duration=5.0)

    @classmethod
    def tearDownClass(cls):
        if cls.test_dir.exists():
            shutil.rmtree(cls.test_dir, ignore_errors=True)

    def setUp(self):
        self.proj_dir = Path(tempfile.mkdtemp(prefix="autodub_p4_proj_"))
        self.proj = Project(self.proj_dir, name="test_p4_proj")
        
        # Setup extracted audio
        src_path = self.proj_dir / "source" / "input.mp4"
        src_path.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy(self.sample_video, src_path)
        
        extractor = RealExtractor()
        extractor.run(self.proj)

    def tearDown(self):
        if self.proj_dir.exists():
            shutil.rmtree(self.proj_dir, ignore_errors=True)

    def test_01_srt_timestamp_formatter(self):
        self.assertEqual(format_srt_timestamp(0.0), "00:00:00,000")
        self.assertEqual(format_srt_timestamp(3.52), "00:00:03,520")
        self.assertEqual(format_srt_timestamp(3661.123), "01:01:01,123")

    def test_02_srt_validator(self):
        valid_srt = "1\n00:00:00,520 --> 00:00:03,840\nHello everyone\n\n2\n00:00:04,120 --> 00:00:07,300\nWelcome\n"
        invalid_srt = "INVALID SRT TEXT CONTENT"
        self.assertTrue(validate_srt_content(valid_srt))
        self.assertFalse(validate_srt_content(invalid_srt))

    def test_03_cuda_explicit_failure_handling(self):
        transcriber = RealTranscriber(device="cuda")
        # Override _init_whisper_model to simulate CUDA failure
        def fake_init():
            raise AutoDubError("CUDA device explicitly requested but failed to initialize: CUDA error")
        transcriber._init_whisper_model = fake_init

        with self.assertRaises(AutoDubError):
            transcriber.run(self.proj)

    def test_04_cpu_fallback_logic(self):
        transcriber = RealTranscriber(device="auto")
        # Mock WhisperModel to simulate CUDA fail -> CPU fallback
        transcriber.whisper_model = MockWhisperModel()
        transcriber.active_device = "cpu"
        transcriber.run(self.proj)

        self.assertEqual(transcriber.active_device, "cpu")
        srt_file = self.proj_dir / "transcript" / "original.srt"
        self.assertTrue(srt_file.exists())

    def test_05_audio_validation_check(self):
        audio_wav = self.proj_dir / "audio" / "original.wav"
        audio_wav.unlink()

        transcriber = RealTranscriber()
        transcriber.whisper_model = MockWhisperModel()
        with self.assertRaises(AutoDubError):
            transcriber.run(self.proj)

    def test_06_chunk_creation_and_offsets(self):
        transcriber = RealTranscriber(chunk_duration=2)
        transcriber.whisper_model = MockWhisperModel()
        transcriber.run(self.proj)

        srt_file = self.proj_dir / "transcript" / "original.srt"
        self.assertTrue(srt_file.exists())
        
        segments = self.proj.data.get("segments", [])
        self.assertGreater(len(segments), 0)
        self.assertEqual(segments[0]["id"], 1)

    def test_07_partial_checkpoint_and_resume(self):
        # Create a partial checkpoint file
        partial_json = self.proj_dir / "transcript" / "original.partial.json"
        partial_json.parent.mkdir(parents=True, exist_ok=True)
        with open(partial_json, "w", encoding="utf-8") as f:
            json.dump({
                "completed_chunks": [0],
                "segments": [{"id": 1, "start": 0.5, "end": 2.0, "text": "Partially saved segment."}],
                "language": "en",
                "language_probability": 0.99
            }, f)

        transcriber = RealTranscriber(chunk_duration=2)
        transcriber.whisper_model = MockWhisperModel()
        transcriber.run(self.proj)

        srt_file = self.proj_dir / "transcript" / "original.srt"
        self.assertTrue(srt_file.exists())

    def test_08_cancellation_cleanup(self):
        transcriber = RealTranscriber(chunk_duration=2)
        transcriber.whisper_model = MockWhisperModel()

        with self.assertRaises(PipelineCancelledError):
            transcriber.run(self.proj, is_cancelled=lambda: True)

        stage_info = self.proj.get_stage_info("transcribe")
        self.assertEqual(stage_info["status"], StageStatus.CANCELLED.value)

    def test_09_idempotency_and_force(self):
        transcriber = RealTranscriber()
        transcriber.whisper_model = MockWhisperModel()
        transcriber.run(self.proj)

        srt_file = self.proj_dir / "transcript" / "original.srt"
        mtime1 = srt_file.stat().st_mtime

        # Running again without force should skip
        transcriber.run(self.proj)
        mtime2 = srt_file.stat().st_mtime
        self.assertEqual(mtime1, mtime2)

        # Running with force should re-transcribe
        def mock_init():
            transcriber.whisper_model = MockWhisperModel()
        transcriber._init_whisper_model = mock_init
        transcriber.run(self.proj, force=True)
        mtime3 = srt_file.stat().st_mtime
        self.assertNotEqual(mtime2, mtime3)

if __name__ == "__main__":
    unittest.main()
