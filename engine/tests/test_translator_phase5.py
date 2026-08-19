import json
import os
import shutil
import tempfile
import unittest
from pathlib import Path

from autodub.models.project import Project
from autodub.pipeline.state import PipelineStage, StageStatus
from autodub.modules.translator import (
    RealTranslator, OllamaClient, clean_translation
)
from autodub.exceptions import (
    AutoDubError,
    PipelineCancelledError,
    OllamaUnavailableError,
    OllamaModelNotFoundError,
    OllamaTimeoutError,
    TranslationFailedError
)

class MockOllamaClient(OllamaClient):
    """Mock OllamaClient for deterministic unit testing without a running Ollama server."""
    def __init__(self, is_running=True, has_model=True, response_map=None, fail_count=0, timeout_trigger=False, base_url=None, **kwargs):
        super().__init__(base_url=base_url or "http://mock-ollama:11434")
        self.is_running = is_running
        self.has_model = has_model
        self.response_map = response_map or {
            "Hello everyone": "Xin chào mọi người",
            "Welcome to AutoDubStudio": "Chào mừng đến với AutoDubStudio",
            "This is a local AI dubbing pipeline": "Đây là quy trình lồng tiếng AI cục bộ"
        }
        self.fail_count = fail_count
        self.calls_made = 0
        self.timeout_trigger = timeout_trigger

    def check_availability(self, model_name: str = "qwen2.5:3b"):
        if not self.is_running:
            return False, "Ollama is not running at http://mock-ollama:11434"
        if not self.has_model:
            return False, f"Ollama model '{model_name}' is not installed."
        return True, ""

    def generate(self, prompt: str, system=None, model="qwen2.5:3b", timeout=120):
        self.calls_made += 1
        if self.timeout_trigger:
            raise OllamaTimeoutError("Ollama generate request timed out after 120 seconds.")
        if self.fail_count > 0 and self.calls_made <= self.fail_count:
            raise TranslationFailedError("Simulated transient network error")

        if prompt in self.response_map:
            return self.response_map[prompt]
        return f"Bản dịch: {prompt} (translated)"

class TestPhase5Translator(unittest.TestCase):
    def setUp(self):
        self.proj_dir = Path(tempfile.mkdtemp(prefix="autodub_p5_proj_"))
        self.proj = Project(self.proj_dir, name="test_p5_proj")
        
        # Setup sample segments and original.srt
        self.sample_segments = [
            {"id": 1, "start": 0.5, "end": 3.2, "text": "Hello everyone"},
            {"id": 2, "start": 3.5, "end": 6.8, "text": "Welcome to AutoDubStudio"},
            {"id": 3, "start": 7.0, "end": 9.5, "text": "This is a local AI dubbing pipeline"}
        ]
        self.proj.data["segments"] = self.sample_segments
        self.proj.save()

        # Write original.srt
        transcript_dir = self.proj_dir / "transcript"
        transcript_dir.mkdir(parents=True, exist_ok=True)
        with open(transcript_dir / "original.srt", "w", encoding="utf-8") as f:
            f.write(
                "1\n00:00:00,500 --> 00:00:03,200\nHello everyone\n\n"
                "2\n00:00:03,500 --> 00:00:06,800\nWelcome to AutoDubStudio\n\n"
                "3\n00:00:07,000 --> 00:00:09,500\nThis is a local AI dubbing pipeline\n"
            )

    def tearDown(self):
        if self.proj_dir.exists():
            shutil.rmtree(self.proj_dir, ignore_errors=True)

    def test_01_clean_translation_formatter(self):
        self.assertEqual(clean_translation("  Xin chào mọi người  "), "Xin chào mọi người")
        self.assertEqual(clean_translation("```vietnamese\nXin chào\n```"), "Xin chào")
        self.assertEqual(clean_translation('"Xin chào mọi người"'), "Xin chào mọi người")
        self.assertEqual(clean_translation("Bản dịch: Xin chào mọi người"), "Xin chào mọi người")

    def test_02_ollama_unreachable_error(self):
        mock_client = MockOllamaClient(is_running=False)
        translator = RealTranslator(client=mock_client)

        with self.assertRaises(OllamaUnavailableError):
            translator.run(self.proj)

        stage_info = self.proj.get_stage_info("translate")
        self.assertEqual(stage_info["status"], StageStatus.FAILED.value)

    def test_03_model_not_found_error(self):
        mock_client = MockOllamaClient(is_running=True, has_model=False)
        translator = RealTranslator(model_name="nonexistent:model", client=mock_client)

        with self.assertRaises(OllamaModelNotFoundError):
            translator.run(self.proj)

        stage_info = self.proj.get_stage_info("translate")
        self.assertEqual(stage_info["status"], StageStatus.FAILED.value)

    def test_04_successful_translation(self):
        mock_client = MockOllamaClient()
        translator = RealTranslator(client=mock_client)
        translator.run(self.proj)

        stage_info = self.proj.get_stage_info("translate")
        self.assertEqual(stage_info["status"], StageStatus.COMPLETED.value)

        translated_srt = self.proj_dir / "transcript" / "translated.srt"
        self.assertTrue(translated_srt.exists())

        segments = self.proj.data.get("segments", [])
        self.assertEqual(segments[0]["translation"], "Xin chào mọi người")
        self.assertEqual(segments[1]["translation"], "Chào mừng đến với AutoDubStudio")

    def test_05_empty_segment_handling(self):
        self.proj.data["segments"].append({"id": 4, "start": 10.0, "end": 12.0, "text": "   "})
        self.proj.save()

        transcript_dir = self.proj_dir / "transcript"
        with open(transcript_dir / "original.srt", "a", encoding="utf-8") as f:
            f.write("\n\n4\n00:00:10,000 --> 00:00:12,000\n   ")

        mock_client = MockOllamaClient()
        translator = RealTranslator(client=mock_client)
        translator.run(self.proj)

        segments = self.proj.data.get("segments", [])
        self.assertEqual(segments[3]["translation"], "")

    def test_06_timeout_handling(self):
        mock_client = MockOllamaClient(timeout_trigger=True)
        translator = RealTranslator(client=mock_client, max_retries=1)

        with self.assertRaises(TranslationFailedError):
            translator.run(self.proj)

    def test_07_transient_retry_success(self):
        # Fail 2 times then succeed on 3rd attempt
        mock_client = MockOllamaClient(fail_count=2)
        translator = RealTranslator(client=mock_client, max_retries=3)
        translator.run(self.proj)

        stage_info = self.proj.get_stage_info("translate")
        self.assertEqual(stage_info["status"], StageStatus.COMPLETED.value)

    def test_08_checkpoint_and_resume(self):
        # Save partial checkpoint with segment 1 already translated
        partial_json = self.proj_dir / "transcript" / "translation.partial.json"
        with open(partial_json, "w", encoding="utf-8") as f:
            json.dump({
                "model": "qwen2.5:3b",
                "completed_segments": [1],
                "translations": {"1": "Xin chào (pre-cached)"}
            }, f)

        mock_client = MockOllamaClient()
        translator = RealTranslator(client=mock_client)
        translator.run(self.proj)

        segments = self.proj.data.get("segments", [])
        self.assertEqual(segments[0]["translation"], "Xin chào (pre-cached)")
        self.assertEqual(segments[1]["translation"], "Chào mừng đến với AutoDubStudio")

    def test_09_cancellation_preserves_checkpoint(self):
        mock_client = MockOllamaClient()
        translator = RealTranslator(client=mock_client)

        with self.assertRaises(PipelineCancelledError):
            translator.run(self.proj, is_cancelled=lambda: True)

        stage_info = self.proj.get_stage_info("translate")
        self.assertEqual(stage_info["status"], StageStatus.CANCELLED.value)

        partial_json = self.proj_dir / "transcript" / "translation.partial.json"
        self.assertTrue(partial_json.exists())

    def test_10_idempotency_and_force(self):
        mock_client = MockOllamaClient()
        translator = RealTranslator(client=mock_client)
        translator.run(self.proj)

        translated_srt = self.proj_dir / "transcript" / "translated.srt"
        mtime1 = translated_srt.stat().st_mtime

        # Run again without force should skip
        translator.run(self.proj)
        mtime2 = translated_srt.stat().st_mtime
        self.assertEqual(mtime1, mtime2)

        # Run with force should re-translate
        translator.run(self.proj, force=True)
        mtime3 = translated_srt.stat().st_mtime
        self.assertNotEqual(mtime2, mtime3)

    def test_11_timestamp_preservation_and_segment_count(self):
        mock_client = MockOllamaClient()
        translator = RealTranslator(client=mock_client)
        translator.run(self.proj)

        with open(self.proj_dir / "transcript" / "original.srt", "r", encoding="utf-8") as f:
            orig_srt = f.read()
        with open(self.proj_dir / "transcript" / "translated.srt", "r", encoding="utf-8") as f:
            trans_srt = f.read()

        orig_blocks = orig_srt.strip().split("\n\n")
        trans_blocks = trans_srt.strip().split("\n\n")

        self.assertEqual(len(orig_blocks), len(trans_blocks))

        for o_b, t_b in zip(orig_blocks, trans_blocks):
            o_lines = o_b.strip().split("\n")
            t_lines = t_b.strip().split("\n")
            self.assertEqual(o_lines[0], t_lines[0]) # ID match
            self.assertEqual(o_lines[1], t_lines[1]) # Timestamp match

if __name__ == "__main__":
    unittest.main()
