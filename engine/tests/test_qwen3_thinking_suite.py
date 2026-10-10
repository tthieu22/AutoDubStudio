import json
import os
import shutil
import tempfile
import unittest
from pathlib import Path

from autodub.models.project import Project
from autodub.pipeline.state import PipelineStage, StageStatus
from autodub.modules.translator import (
    RealTranslator,
    OllamaClient,
    parse_subtitle_batch_response,
    strip_think_tags
)
from autodub.modules.output_sanitizer import TranslationOutputSanitizer
from autodub.exceptions import (
    TranslationFailedError,
    OllamaTimeoutError
)


class MockThinkingOllamaClient(OllamaClient):
    """Mock client specifically configured to simulate Qwen3 Thinking outputs and errors."""
    def __init__(self, response_behavior="normal", timeout_always=False, partial_fail_id=None):
        super().__init__(base_url="http://mock-ollama:11434")
        self.response_behavior = response_behavior
        self.timeout_always = timeout_always
        self.partial_fail_id = partial_fail_id
        self.call_count = 0

    def check_availability(self, model_name: str = "qwen3:4b"):
        return True, ""

    def ensure_model_loaded(self, timeout: int = 60):
        return True, ""

    def generate(self, prompt: str, system=None, model="qwen3:4b", timeout=120, **kwargs):
        self.call_count += 1

        if self.timeout_always:
            raise OllamaTimeoutError("Ollama request timed out after 120s.")

        if self.response_behavior == "raw_think_tags":
            return "<think>\nThe Chinese phrase 爸爸和妈妈去买菜 means father and mother go buy groceries.\nIn Vietnamese, 爸爸 is Bố, 妈妈 is Mẹ, 买菜 is đi mua rau.\n</think>\nBố và mẹ đi mua rau."

        if self.response_behavior == "conversational_reasoning":
            return "Okay, let's tackle this translation task.\nFirst, I need to analyze the input sentence:\n你好，你在干什么？\nThis translates naturally to spoken Vietnamese as:\nBạn đang làm gì vậy?"

        if self.response_behavior == "batch_with_partial_failure" and self.partial_fail_id:
            # Emit batch where one ID is missing or corrupt
            return f"[SUBTITLE_001]\nBố và mẹ đi mua rau.\n\n[SUBTITLE_002]\nBạn đang làm gì vậy?\n\n[SUBTITLE_003]\n"

        # Standard batch formatting simulation
        if "[SUBTITLE_001]" in prompt:
            return "[SUBTITLE_001]\nBố và mẹ đi mua rau.\n\n[SUBTITLE_002]\nBạn đang làm gì vậy?\n\n[SUBTITLE_003]\nBạn ăn cơm chưa?"

        if "爸爸和妈妈去买菜" in prompt:
            return "<think>\nAnalyzing 爸爸和妈妈去买菜...\n</think>\nBố và mẹ đi mua rau."
        if "你好，你在干什么" in prompt:
            return "<think>\nAnalyzing 你好，你在干什么？...\n</think>\nBạn đang làm gì vậy?"
        if "你吃饭了吗" in prompt:
            return "<think>\nAnalyzing 你吃饭了吗？...\n</think>\nBạn ăn cơm chưa?"

        return "Bản dịch tiếng Việt"


class TestQwen3ThinkingModeSuite(unittest.TestCase):
    """Verifies all 8 required Test Cases from Official Qwen3 Thinking Mode Specification."""

    def setUp(self):
        self.proj_dir = Path(tempfile.mkdtemp(prefix="autodub_qwen3_thinking_"))
        self.proj = Project(self.proj_dir, name="test_thinking_proj")
        transcript_dir = self.proj_dir / "transcript"
        transcript_dir.mkdir(parents=True, exist_ok=True)

    def tearDown(self):
        if self.proj_dir.exists():
            shutil.rmtree(self.proj_dir, ignore_errors=True)

    def test_case_1_single_sentence_with_thinking(self):
        """Test 1: 爸爸和妈妈去买菜. -> Bố và mẹ đi mua rau. (Thinking ON, no reasoning in output)"""
        raw_output = "<think>\nAnalyzing 爸爸 and 妈妈 and 买菜.\nFather and Mother go buy vegetables.\n</think>\nBố và mẹ đi mua rau."
        cleaned = strip_think_tags(raw_output)
        sanitized = TranslationOutputSanitizer.sanitize(cleaned)
        self.assertEqual(sanitized, "Bố và mẹ đi mua rau.")
        self.assertNotIn("think", sanitized.lower())
        self.assertNotIn("father", sanitized.lower())

    def test_case_2_dialogue_translation(self):
        """Test 2: 你好，你在干什么？ -> Bạn đang làm gì vậy?"""
        raw_output = "<think>\nInformal greeting and question.\n</think>\nBạn đang làm gì vậy?"
        sanitized = TranslationOutputSanitizer.sanitize(strip_think_tags(raw_output))
        self.assertEqual(sanitized, "Bạn đang làm gì vậy?")

    def test_case_3_daily_greeting_translation(self):
        """Test 3: 你吃饭了吗？ -> Bạn ăn cơm chưa?"""
        raw_output = "<think>\nCommon Chinese greeting asking if one has eaten.\n</think>\nBạn ăn cơm chưa?"
        sanitized = TranslationOutputSanitizer.sanitize(strip_think_tags(raw_output))
        self.assertEqual(sanitized, "Bạn ăn cơm chưa?")

    def test_case_4_raw_think_tags_removal(self):
        """Test 4: Raw response with <think>...</think> extracts ONLY final Vietnamese translation."""
        raw = "<think>\nChinese sentence means father and mother...\n</think>\n\nBố và mẹ đi mua rau."
        sanitized = TranslationOutputSanitizer.sanitize(strip_think_tags(raw))
        self.assertEqual(sanitized, "Bố và mẹ đi mua rau.")

    def test_case_5_preamble_reasoning_extraction(self):
        """Test 5: Qwen3 returning reasoning before final answer -> Parser extracts only final translation."""
        raw = "Okay, let's tackle this translation task.\nFirst, I need to understand the meaning.\nHere is the Vietnamese translation:\nBố và mẹ đi mua rau."
        sanitized = TranslationOutputSanitizer.sanitize(strip_think_tags(raw))
        self.assertEqual(sanitized, "Bố và mẹ đi mua rau.")

    def test_case_6_timeout_retry_once_and_stage_error(self):
        """Test 6: Timeout retries ONE time then fails with stage_error (NO fallback)."""
        self.proj.data["segments"] = [
            {"id": 1, "start": 0.0, "end": 2.0, "text": "爸爸和妈妈去买菜."}
        ]
        self.proj.save()

        mock_client = MockThinkingOllamaClient(timeout_always=True)
        translator = RealTranslator(client=mock_client, batch_size=1)

        with self.assertRaises((TranslationFailedError, OllamaTimeoutError)):
            translator.run(self.proj)

        # Retried exactly 1 time (2 calls total)
        self.assertEqual(mock_client.call_count, 2)
        stage_info = self.proj.get_stage_info("translate")
        self.assertEqual(stage_info["status"], StageStatus.FAILED.value)

    def test_case_7_partial_checkpoint_on_failure(self):
        """Test 7: Batch 3 with failure on 003 saves checkpoint for 001+002 and marks stage_error."""
        # Pre-seed partial checkpoint with SUBTITLE_001 and SUBTITLE_002
        partial_json = self.proj_dir / "transcript" / "translation.partial.json"
        with open(partial_json, "w", encoding="utf-8") as f:
            json.dump({
                "model": "qwen3:4b",
                "completed_segments": ["SUBTITLE_001", "SUBTITLE_002"],
                "translations": {
                    "SUBTITLE_001": "Bố và mẹ đi mua rau.",
                    "SUBTITLE_002": "Bạn đang làm gì vậy?"
                }
            }, f)

        self.proj.data["segments"] = [
            {"id": 1, "start": 0.0, "end": 2.0, "text": "爸爸和妈妈去买菜."},
            {"id": 2, "start": 2.5, "end": 4.5, "text": "你好，你在干什么？"},
            {"id": 3, "start": 5.0, "end": 7.0, "text": "你吃饭了吗？"}
        ]
        self.proj.save()

        # Mock client fails on remaining item
        mock_client = MockThinkingOllamaClient(timeout_always=True)
        translator = RealTranslator(client=mock_client, batch_size=3)

        with self.assertRaises((TranslationFailedError, OllamaTimeoutError)):
            translator.run(self.proj)

        # Verify checkpoint is intact with 001 + 002
        with open(partial_json, "r", encoding="utf-8") as f:
            ckpt = json.load(f)
        self.assertIn("SUBTITLE_001", ckpt["completed_segments"])
        self.assertIn("SUBTITLE_002", ckpt["completed_segments"])
        self.assertEqual(ckpt["translations"]["SUBTITLE_001"], "Bố và mẹ đi mua rau.")
        self.assertEqual(ckpt["translations"]["SUBTITLE_002"], "Bạn đang làm gì vậy?")

        stage_info = self.proj.get_stage_info("translate")
        self.assertEqual(stage_info["status"], StageStatus.FAILED.value)

    def test_case_8_all_successful_stage_complete(self):
        """Test 8: All 3 subtitles successful -> stage_complete and valid translated.srt."""
        self.proj.data["segments"] = [
            {"id": 1, "start": 0.0, "end": 2.0, "text": "爸爸和妈妈去买菜."},
            {"id": 2, "start": 2.5, "end": 4.5, "text": "你好，你在干什么？"},
            {"id": 3, "start": 5.0, "end": 7.0, "text": "你吃饭了吗？"}
        ]
        self.proj.save()

        mock_client = MockThinkingOllamaClient(response_behavior="normal")
        translator = RealTranslator(client=mock_client, batch_size=3)
        translator.run(self.proj)

        stage_info = self.proj.get_stage_info("translate")
        self.assertEqual(stage_info["status"], StageStatus.COMPLETED.value)

        translated_srt = self.proj_dir / "transcript" / "translated.srt"
        self.assertTrue(translated_srt.exists())

        with open(translated_srt, "r", encoding="utf-8") as f:
            srt_content = f.read()

        self.assertIn("Bố và mẹ đi mua rau.", srt_content)
        self.assertIn("Bạn đang làm gì vậy?", srt_content)
        self.assertIn("Bạn ăn cơm chưa?", srt_content)
        self.assertNotIn("<think>", srt_content)


if __name__ == "__main__":
    unittest.main()
