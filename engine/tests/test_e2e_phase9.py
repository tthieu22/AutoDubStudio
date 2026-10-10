import json
import os
import shutil
import tempfile
import unittest
import wave
import subprocess
import time
from pathlib import Path
from typing import Any

from autodub.models.project import Project
from autodub.pipeline.manager import PipelineManager
from autodub.pipeline.state import PipelineStage, StageStatus
from autodub.utils.ffmpeg import FFmpegRunner


def create_synthetic_mp4(path: Path, duration: float = 3.0, runner: Any = None):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    runner = runner or FFmpegRunner()
    cmd = [
        str(runner.ffmpeg_path), "-y",
        "-f", "lavfi", "-i", f"color=c=blue:s=320x240:r=15:d={duration}",
        "-f", "lavfi", "-i", f"anullsrc=r=16000:cl=mono:d={duration}",
        "-c:v", "libx264", "-c:a", "aac", "-shortest",
        str(path)
    ]
    subprocess.run(cmd, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)


def create_synthetic_wav(path: Path, duration: float = 3.0, sample_rate: int = 16000):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    num_frames = int(max(0.01, duration) * sample_rate)
    frame_data = b"\x10\x00"
    with wave.open(str(path), "wb") as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(sample_rate)
        wf.writeframes(frame_data * num_frames)


class TestPhase9E2E(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.mkdtemp(prefix="autodub_test_e2e_p9_")
        self.proj_dir = Path(self.temp_dir) / "test_e2e_project"
        self.proj_dir.mkdir(parents=True, exist_ok=True)
        self.runner = FFmpegRunner()

    def tearDown(self):
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_01_full_e2e_pipeline_execution(self):
        mgr = PipelineManager(str(self.proj_dir), step_delay=0.001)
        src_file = self.proj_dir / "source" / "input.mp4"
        create_synthetic_mp4(src_file, duration=3.0, runner=self.runner)

        # Pre-populate synthetic artifacts so AI model network calls are skipped
        create_synthetic_wav(self.proj_dir / "audio" / "original.wav", 3.0)
        (self.proj_dir / "transcript").mkdir(parents=True, exist_ok=True)
        (self.proj_dir / "transcript" / "original.srt").write_text("1\n00:00:00,000 --> 00:00:03,000\nHello world\n", encoding="utf-8")
        (self.proj_dir / "transcript" / "translated.srt").write_text("1\n00:00:00,000 --> 00:00:03,000\nXin chao the gioi\n", encoding="utf-8")

        create_synthetic_wav(self.proj_dir / "audio" / "synced" / "combined.wav", 3.0)
        create_synthetic_wav(self.proj_dir / "audio" / "synced" / "000001.wav", 3.0)
        create_synthetic_wav(self.proj_dir / "audio" / "tts" / "000001.wav", 3.0)
        create_synthetic_wav(self.proj_dir / "audio" / "mixed.wav", 3.0)

        for st in ["extract", "transcribe", "translate", "tts", "sync"]:
            mgr.project.update_stage(st, StageStatus.COMPLETED.value, progress=100)

        mgr.project.data["segments"] = [{
            "id": 1,
            "start": 0.0,
            "end": 3.0,
            "text": "Hello world",
            "translated_text": "Xin chao the gioi",
            "tts": {"status": "COMPLETED", "path": "audio/tts/000001.wav"},
            "sync": {"status": "COMPLETED", "path": "audio/synced/000001.wav"}
        }]
        mgr.project.save()

        mgr.run_all()

        final_mp4 = self.proj_dir / "output" / "final.mp4"
        self.assertTrue(final_mp4.exists())
        self.assertGreater(final_mp4.stat().st_size, 0)

        # Check project.json pipeline states
        for stage in ["extract", "transcribe", "translate", "tts", "sync", "render"]:
            st_info = mgr.project.get_stage_info(stage)
            self.assertEqual(st_info["status"], StageStatus.COMPLETED.value)

        # Check timing metadata
        metadata = mgr.project.data.get("metadata", {})
        self.assertIn("timing", metadata)
        self.assertIn("total", metadata["timing"])

    def test_02_idempotent_pipeline_execution(self):
        mgr = PipelineManager(str(self.proj_dir), step_delay=0.001)
        src_file = self.proj_dir / "source" / "input.mp4"
        create_synthetic_mp4(src_file, duration=2.0, runner=self.runner)

        create_synthetic_wav(self.proj_dir / "audio" / "original.wav", 2.0)
        (self.proj_dir / "transcript").mkdir(parents=True, exist_ok=True)
        (self.proj_dir / "transcript" / "original.srt").write_text("1\n00:00:00,000 --> 00:00:02,000\nHi\n", encoding="utf-8")
        (self.proj_dir / "transcript" / "translated.srt").write_text("1\n00:00:00,000 --> 00:00:02,000\nChao\n", encoding="utf-8")
        create_synthetic_wav(self.proj_dir / "audio" / "synced" / "combined.wav", 2.0)
        create_synthetic_wav(self.proj_dir / "audio" / "synced" / "000001.wav", 2.0)
        create_synthetic_wav(self.proj_dir / "audio" / "tts" / "000001.wav", 2.0)
        create_synthetic_wav(self.proj_dir / "audio" / "mixed.wav", 2.0)

        for st in ["extract", "transcribe", "translate", "tts", "sync"]:
            mgr.project.update_stage(st, StageStatus.COMPLETED.value, progress=100)

        mgr.project.data["segments"] = [{
            "id": 1,
            "start": 0.0,
            "end": 2.0,
            "text": "Hi",
            "translated_text": "Chao"
        }]
        mgr.project.save()

        # First run
        mgr.run_all()

        # Second run (Idempotent skip)
        start_t = time.time()
        mgr.run_all()
        second_dur = time.time() - start_t

        self.assertLess(second_dur, 2.0)
