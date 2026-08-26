import shutil
import tempfile
import unittest
from pathlib import Path

from autodub.utils.logging import ProjectLogger, setup_logger

class TestPhase4LoggingSystem(unittest.TestCase):
    def setUp(self):
        self.test_dir = Path(tempfile.mkdtemp(prefix="autodub_p4_test_"))
        self.project_dir = self.test_dir / "project_log_test"

    def tearDown(self):
        if self.test_dir.exists():
            shutil.rmtree(self.test_dir, ignore_errors=True)

    def test_01_multi_file_creation(self):
        plogger = ProjectLogger(self.project_dir, project_id="proj_001")
        plogger.info("pipeline", "Pipeline initialized")
        plogger.info("llm", "Prompting Qwen", scene_id="scene_001", task_id="task_001")
        plogger.info("image", "Generating SD image", scene_id="scene_001", duration=2.45)
        plogger.info("tts", "Synthesizing audio", scene_id="scene_001", duration=0.85)
        plogger.info("ffmpeg", "Rendering video", duration=5.10)
        plogger.error("llm", "LLM timeout error", scene_id="scene_002")

        expected_files = ["pipeline.log", "llm.log", "image.log", "tts.log", "ffmpeg.log", "error.log"]
        for fname in expected_files:
            log_path = self.project_dir / "logs" / fname
            self.assertTrue(log_path.exists(), f"Missing log file: {fname}")
            self.assertGreater(log_path.stat().st_size, 0, f"Log file empty: {fname}")

    def test_02_error_mirroring(self):
        plogger = ProjectLogger(self.project_dir, project_id="proj_002")
        plogger.warning("image", "CUDA VRAM low warning", scene_id="scene_003")
        plogger.error("ffmpeg", "FFmpeg NVENC encode error", duration=1.2)

        error_log = self.project_dir / "logs" / "error.log"
        content = error_log.read_text(encoding="utf-8")
        self.assertIn("[IMAGE]", content)
        self.assertIn("CUDA VRAM low warning", content)
        self.assertIn("[FFMPEG]", content)
        self.assertIn("FFmpeg NVENC encode error", content)

    def test_03_legacy_setup_logger_compatibility(self):
        legacy_log = self.project_dir / "logs" / "pipeline.log"
        logger = setup_logger(legacy_log)
        logger.info("Legacy log entry test")
        self.assertTrue(legacy_log.exists())
        self.assertIn("Legacy log entry test", legacy_log.read_text(encoding="utf-8"))

if __name__ == "__main__":
    unittest.main()
