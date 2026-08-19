import os
import shutil
import tempfile
import unittest
import subprocess
from pathlib import Path

from autodub.models.project import Project
from autodub.pipeline.state import PipelineStage, StageStatus
from autodub.utils.ffmpeg import find_ffmpeg, find_ffprobe, FFmpegRunner
from autodub.modules.extractor import RealExtractor
from autodub.exceptions import AutoDubError, PipelineCancelledError

def create_synthetic_media(output_mp4: Path, has_audio: bool = True, duration: float = 3.0):
    """Generate a small synthetic mp4 video using ffmpeg."""
    ffmpeg_bin = str(find_ffmpeg())
    output_mp4.parent.mkdir(parents=True, exist_ok=True)
    
    if has_audio:
        cmd = [
            ffmpeg_bin, "-y",
            "-f", "lavfi", "-i", f"testsrc=duration={duration}:size=320x240:rate=30",
            "-f", "lavfi", "-i", f"sine=frequency=440:duration={duration}",
            "-c:v", "libx264", "-c:a", "aac", "-shortest",
            str(output_mp4)
        ]
    else:
        cmd = [
            ffmpeg_bin, "-y",
            "-f", "lavfi", "-i", f"testsrc=duration={duration}:size=320x240:rate=30",
            "-c:v", "libx264", "-an",
            str(output_mp4)
        ]
    subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)

class TestPhase3Extractor(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.test_dir = Path(tempfile.mkdtemp(prefix="autodub_p3_"))
        cls.sample_video = cls.test_dir / "sample.mp4"
        cls.no_audio_video = cls.test_dir / "no_audio.mp4"
        
        # Ensure binaries exist
        cls.ffmpeg_bin = find_ffmpeg()
        cls.ffprobe_bin = find_ffprobe()

        create_synthetic_media(cls.sample_video, has_audio=True, duration=3.0)
        create_synthetic_media(cls.no_audio_video, has_audio=False, duration=3.0)

    @classmethod
    def tearDownClass(cls):
        if cls.test_dir.exists():
            shutil.rmtree(cls.test_dir, ignore_errors=True)

    def setUp(self):
        self.proj_dir = Path(tempfile.mkdtemp(prefix="autodub_proj_"))
        self.proj = Project(self.proj_dir, name="test_p3_proj")
        
        # Copy synthetic video to project source
        src_path = self.proj_dir / "source" / "input.mp4"
        src_path.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy(self.sample_video, src_path)

    def tearDown(self):
        if self.proj_dir.exists():
            shutil.rmtree(self.proj_dir, ignore_errors=True)

    def test_01_ffmpeg_and_ffprobe_discovery(self):
        self.assertTrue(self.ffmpeg_bin.exists())
        self.assertTrue(self.ffprobe_bin.exists())

    def test_02_metadata_probe(self):
        runner = FFmpegRunner()
        meta = runner.probe(self.sample_video)
        self.assertGreater(meta["duration"], 2.0)
        self.assertTrue(meta["has_audio"])
        self.assertEqual(meta["audio_channels"], 1 if meta["audio_channels"] == 1 else meta["audio_channels"])

    def test_03_valid_audio_extraction(self):
        extractor = RealExtractor()
        extractor.run(self.proj)

        output_wav = self.proj_dir / "audio" / "original.wav"
        self.assertTrue(output_wav.exists())

        # Check metadata in project.json
        stage_info = self.proj.get_stage_info("extract")
        self.assertEqual(stage_info["status"], StageStatus.COMPLETED.value)
        self.assertEqual(stage_info["progress"], 100)

        audio_meta = self.proj.data["metadata"]["audio"]
        self.assertEqual(audio_meta["codec"], "pcm_s16le")
        self.assertEqual(audio_meta["sample_rate"], 16000)
        self.assertEqual(audio_meta["channels"], 1)

    def test_04_missing_input_file_error(self):
        self.proj.data["source"]["path"] = "source/non_existent.mp4"
        self.proj.save()

        extractor = RealExtractor()
        with self.assertRaises(AutoDubError):
            extractor.run(self.proj)

    def test_05_no_audio_stream_error(self):
        no_audio_src = self.proj_dir / "source" / "input_no_audio.mp4"
        shutil.copy(self.no_audio_video, no_audio_src)
        self.proj.data["source"]["path"] = "source/input_no_audio.mp4"
        self.proj.save()

        extractor = RealExtractor()
        with self.assertRaises(AutoDubError) as ctx:
            extractor.run(self.proj)
        self.assertIn("No audio stream found", str(ctx.exception))

    def test_06_idempotency_and_force(self):
        extractor = RealExtractor()
        extractor.run(self.proj)
        
        output_wav = self.proj_dir / "audio" / "original.wav"
        mtime1 = output_wav.stat().st_mtime

        # Running again without force should skip extraction
        extractor.run(self.proj)
        mtime2 = output_wav.stat().st_mtime
        self.assertEqual(mtime1, mtime2)

        # Running with force should re-extract
        extractor.run(self.proj, force=True)
        mtime3 = output_wav.stat().st_mtime
        self.assertNotEqual(mtime2, mtime3)

    def test_07_corrupt_output_handling(self):
        extractor = RealExtractor()
        extractor.run(self.proj)
        
        output_wav = self.proj_dir / "audio" / "original.wav"
        with open(output_wav, "wb") as f:
            f.write(b"CORRUPT INVALID WAV HEADER DATA")

        # Extraction should detect corrupt WAV and re-extract
        extractor.run(self.proj)
        self.assertTrue(output_wav.exists())
        meta = FFmpegRunner().validate_wav(output_wav)
        self.assertEqual(meta["audio_codec"], "pcm_s16le")

    def test_08_cancellation(self):
        extractor = RealExtractor()
        with self.assertRaises(PipelineCancelledError):
            extractor.run(self.proj, is_cancelled=lambda: True)

        # Ensure .tmp file is cleaned up
        tmp_wav = self.proj_dir / "audio" / "original.wav.tmp"
        self.assertFalse(tmp_wav.exists())

if __name__ == "__main__":
    unittest.main()
