import sys
import wave
import json
import shutil
import tempfile
import unittest
from pathlib import Path
from typing import Optional, Tuple
from unittest.mock import patch, MagicMock

# Add engine directory to path
engine_dir = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(engine_dir))

from autodub.models.project import Project
from autodub.pipeline.manager import PipelineManager
from autodub.pipeline.state import PipelineStage, StageStatus
from autodub.modules.tts import RealTTS, PiperClient, validate_wav_file
from autodub.exceptions import (
    PiperUnavailableError,
    PiperVoiceNotFoundError,
    PiperSynthesisError,
    PiperInvalidOutputError,
    PiperTimeoutError,
    TTSSynthesisFailedError,
    PipelineCancelledError
)


class MockPiperClient(PiperClient):
    """Mock Piper Client for unit testing offline."""

    def __init__(self, is_available: bool = True, voice_available: bool = True, fail_segments: set = None, timeout_segments: set = None):
        self.is_available = is_available
        self.voice_available = voice_available
        self.fail_segments = fail_segments or set()
        self.timeout_segments = timeout_segments or set()
        self.synthesize_calls = []
        super().__init__()

    def find_executable(self) -> Optional[Path]:
        if self.is_available:
            return Path("/mock/piper.exe")
        return None

    def find_voice(self, voice_name: str) -> Tuple[Optional[Path], Optional[Path]]:
        if self.voice_available:
            return (Path(f"/mock/{voice_name}.onnx"), Path(f"/mock/{voice_name}.onnx.json"))
        return (None, None)

    def check_availability(self, voice_name: str) -> Tuple[bool, str, int]:
        if not self.is_available:
            return False, "Piper TTS executable not found in runtime/piper/ or system PATH.", 22050
        if not self.voice_available:
            return False, f"Piper voice model '{voice_name}' not found.", 22050
        return True, "", 22050

    def synthesize(
        self,
        text: str,
        output_wav_path: Path,
        voice_name: str,
        timeout: int = 120,
        speaker: Optional[str] = None
    ) -> float:
        self.synthesize_calls.append({"text": text, "output": output_wav_path, "voice": voice_name})

        filename = output_wav_path.name
        seg_id = int(filename.split(".")[0]) if filename.split(".")[0].isdigit() else 1

        if seg_id in self.timeout_segments:
            raise PiperTimeoutError(f"Piper synthesis process timed out after {timeout} seconds.")

        if seg_id in self.fail_segments:
            raise PiperSynthesisError(f"Simulated Piper synthesis failure for segment {seg_id}")

        # Generate a valid 1.0 second 22050Hz mono WAV file
        output_wav_path.parent.mkdir(parents=True, exist_ok=True)
        with wave.open(str(output_wav_path), "wb") as wf:
            wf.setnchannels(1)
            wf.setsampwidth(2)
            wf.setframerate(22050)
            wf.writeframes(b"\x00\x00" * 22050)

        return 0.05


class TestPhase6TTS(unittest.TestCase):

    def setUp(self):
        self.test_dir = Path(tempfile.mkdtemp(prefix="autodub_test_tts_"))
        self.mgr = PipelineManager(str(self.test_dir / "test_project"))
        self.project = self.mgr.project

        # Populate synthetic segments in project
        self.project.data["segments"] = [
            {"id": 1, "start": 0.0, "end": 2.5, "text": "Hello world", "translation": "Xin chào thế giới"},
            {"id": 2, "start": 2.5, "end": 5.0, "text": "Welcome to AutoDubStudio", "translation": "Chào mừng đến với AutoDubStudio"},
            {"id": 3, "start": 5.0, "end": 8.0, "text": "Vietnamese accents test: ấ ầ ẩ ẫ ậ ế ề ể ễ ệ", "translation": "Kiểm tra dấu tiếng Việt: ấ ầ ẩ ẫ ậ ế ề ể ễ ệ"}
        ]
        self.project.save()

    def tearDown(self):
        if self.test_dir.exists():
            shutil.rmtree(self.test_dir, ignore_errors=True)

    def test_01_piper_executable_discovery(self):
        client = PiperClient()
        exe = client.find_executable()
        # Does not fail if not installed on system, tests return type
        self.assertTrue(exe is None or isinstance(exe, Path))

    def test_02_voice_model_discovery(self):
        client = PiperClient()
        onnx_p, json_p = client.find_voice("nonexistent_voice")
        self.assertIsNone(onnx_p)
        self.assertIsNone(json_p)

    def test_03_missing_piper_raises_error(self):
        mock_client = MockPiperClient(is_available=False)
        tts = RealTTS(client=mock_client)
        with self.assertRaises(PiperUnavailableError):
            tts.run(self.project)

    def test_04_missing_voice_raises_error(self):
        mock_client = MockPiperClient(is_available=True, voice_available=False)
        tts = RealTTS(client=mock_client)
        with self.assertRaises(PiperVoiceNotFoundError):
            tts.run(self.project)

    def test_05_successful_synthesis(self):
        mock_client = MockPiperClient()
        tts = RealTTS(client=mock_client)
        elapsed = tts.run(self.project)

        self.assertGreaterEqual(elapsed, 0.0)
        self.assertEqual(self.project.get_stage_info("tts")["status"], StageStatus.COMPLETED.value)
        
        # Verify 3 WAV files generated
        audio_tts_dir = self.project.project_dir / "audio" / "tts"
        for i in range(1, 4):
            wav_path = audio_tts_dir / f"{i:06d}.wav"
            self.assertTrue(wav_path.exists())
            info = validate_wav_file(wav_path)
            self.assertEqual(info["sample_rate"], 22050)
            self.assertAlmostEqual(info["duration"], 1.0, places=1)

    def test_06_wav_validation(self):
        valid_wav = self.test_dir / "valid.wav"
        with wave.open(str(valid_wav), "wb") as wf:
            wf.setnchannels(1)
            wf.setsampwidth(2)
            wf.setframerate(22050)
            wf.writeframes(b"\x00\x00" * 22050)

        info = validate_wav_file(valid_wav)
        self.assertEqual(info["channels"], 1)
        self.assertEqual(info["sample_rate"], 22050)

        # Corrupt file test
        corrupt_wav = self.test_dir / "corrupt.wav"
        with open(corrupt_wav, "wb") as f:
            f.write(b"NOT A WAV FILE")

        with self.assertRaises(PiperInvalidOutputError):
            validate_wav_file(corrupt_wav)

    def test_07_empty_segment_handling(self):
        self.project.data["segments"] = [
            {"id": 1, "start": 0.0, "end": 1.0, "text": "  ", "translation": "   "},
            {"id": 2, "start": 1.0, "end": 3.0, "text": "Valid text", "translation": "Văn bản hợp lệ"}
        ]
        self.project.save()

        mock_client = MockPiperClient()
        tts = RealTTS(client=mock_client)
        tts.run(self.project)

        # Segment 1 should be marked SKIPPED in metadata
        seg1 = self.project.data["segments"][0]
        self.assertEqual(seg1["tts"]["status"], "SKIPPED")
        self.assertEqual(seg1["tts"]["reason"], "EMPTY_TEXT")

        # Only 1 call to piper synthesize for segment 2
        self.assertEqual(len(mock_client.synthesize_calls), 1)

    def test_08_atomic_output(self):
        mock_client = MockPiperClient()
        tts = RealTTS(client=mock_client)
        tts.run(self.project)

        audio_tts_dir = self.project.project_dir / "audio" / "tts"
        # Temp files should have been cleaned up / renamed
        tmp_files = list(audio_tts_dir.glob("*.tmp"))
        self.assertEqual(len(tmp_files), 0)

    def test_09_checkpoint_creation(self):
        mock_client = MockPiperClient()
        tts = RealTTS(client=mock_client)
        tts.run(self.project)

        # Checkpoint is cleaned on successful stage completion, so test partial progress
        partial_json = self.project.project_dir / "audio" / "tts" / "tts.partial.json"
        # Save explicit checkpoint to test file format
        tts._save_partial_checkpoint(partial_json, "vi_VN-viss-low", "vi", [1, 2], {"1": {"duration": 1.0}})
        self.assertTrue(partial_json.exists())

        with open(partial_json, "r", encoding="utf-8") as f:
            data = json.load(f)
            self.assertEqual(data["completed_segments"], [1, 2])
            self.assertEqual(data["engine"], "piper")

    def test_10_resume_skips_completed_segments(self):
        audio_tts_dir = self.project.project_dir / "audio" / "tts"
        audio_tts_dir.mkdir(parents=True, exist_ok=True)
        partial_json = audio_tts_dir / "tts.partial.json"

        # Pre-create completed WAV for segment 1
        wav1 = audio_tts_dir / "000001.wav"
        with wave.open(str(wav1), "wb") as wf:
            wf.setnchannels(1)
            wf.setsampwidth(2)
            wf.setframerate(22050)
            wf.writeframes(b"\x00\x00" * 22050)

        tts = RealTTS(client=MockPiperClient())
        tts._save_partial_checkpoint(partial_json, "vi_VN-viss-low", "vi", [1], {"1": {"duration": 1.0}})

        mock_client = MockPiperClient()
        tts.client = mock_client
        tts.run(self.project)

        # Only segments 2 and 3 should be synthesized
        self.assertEqual(len(mock_client.synthesize_calls), 2)

    def test_11_retry_on_transient_failure(self):
        # Segment 2 fails twice before succeeding
        mock_client = MockPiperClient()
        fail_count = 0
        original_synth = mock_client.synthesize

        def flaky_synthesize(text, output_wav_path, voice_name, timeout=120, speaker=None):
            nonlocal fail_count
            if "000002.wav" in output_wav_path.name and fail_count < 2:
                fail_count += 1
                raise PiperSynthesisError("Transient GPU / process error")
            return original_synth(text, output_wav_path, voice_name, timeout, speaker)

        mock_client.synthesize = flaky_synthesize
        tts = RealTTS(client=mock_client)
        tts.run(self.project)

        self.assertEqual(self.project.get_stage_info("tts")["status"], StageStatus.COMPLETED.value)
        self.assertEqual(fail_count, 2)

    def test_12_timeout_handling(self):
        mock_client = MockPiperClient(timeout_segments={1})
        tts = RealTTS(client=mock_client)

        with self.assertRaises(TTSSynthesisFailedError):
            tts.run(self.project)

        self.assertEqual(self.project.get_stage_info("tts")["status"], StageStatus.FAILED.value)

    def test_13_cancellation_support(self):
        mock_client = MockPiperClient()
        tts = RealTTS(client=mock_client)

        def cancel_check():
            return True

        with self.assertRaises(PipelineCancelledError):
            tts.run(self.project, is_cancelled=cancel_check)

        self.assertEqual(self.project.get_stage_info("tts")["status"], StageStatus.CANCELLED.value)

    def test_14_idempotency_skip_existing_completed(self):
        mock_client = MockPiperClient()
        tts = RealTTS(client=mock_client)
        tts.run(self.project)

        # Second run should finish instantly without synthesizing
        mock_client.synthesize_calls.clear()
        elapsed = tts.run(self.project)
        self.assertEqual(elapsed, 0.0)
        self.assertEqual(len(mock_client.synthesize_calls), 0)

    def test_15_force_flag_retranslates_and_resynthesizes(self):
        mock_client = MockPiperClient()
        tts = RealTTS(client=mock_client)
        tts.run(self.project)

        # Second run with force=True should re-synthesize all 3 segments
        mock_client.synthesize_calls.clear()
        tts.run(self.project, force=True)
        self.assertEqual(len(mock_client.synthesize_calls), 3)

    def test_16_project_json_update(self):
        mock_client = MockPiperClient()
        tts = RealTTS(client=mock_client)
        tts.run(self.project)

        self.assertIn("tts", self.project.data)
        self.assertEqual(self.project.data["tts"]["completed_segments"], 3)
        self.assertEqual(self.project.data["tts"]["engine"], "piper")

        # Verify each segment has tts metadata
        for seg in self.project.data["segments"]:
            self.assertIn("tts", seg)
            self.assertEqual(seg["tts"]["format"], "wav")

    def test_17_unicode_vietnamese_characters(self):
        vietnamese_text = "Thí nghiệm tiếng Việt: ă â ê ô ơ ư đ á à ả ã ạ ấ ầ ẩ ẫ ậ"
        self.project.data["segments"] = [
            {"id": 1, "start": 0.0, "end": 3.0, "text": vietnamese_text, "translation": vietnamese_text}
        ]
        self.project.save()

        mock_client = MockPiperClient()
        tts = RealTTS(client=mock_client)
        tts.run(self.project)

        self.assertEqual(len(mock_client.synthesize_calls), 1)
        self.assertEqual(mock_client.synthesize_calls[0]["text"], vietnamese_text)

    def test_18_invalid_wav_trigger_re_synthesis(self):
        audio_tts_dir = self.project.project_dir / "audio" / "tts"
        audio_tts_dir.mkdir(parents=True, exist_ok=True)
        partial_json = audio_tts_dir / "tts.partial.json"

        # Pre-create corrupted WAV for segment 1
        wav1 = audio_tts_dir / "000001.wav"
        with open(wav1, "wb") as f:
            f.write(b"CORRUPT HEADER DATA")

        tts = RealTTS(client=MockPiperClient())
        tts._save_partial_checkpoint(partial_json, "vi_VN-viss-low", "vi", [1], {"1": {"duration": 1.0}})

        mock_client = MockPiperClient()
        tts.client = mock_client
        tts.run(self.project)

        # Segment 1 should be re-synthesized because file was invalid
        self.assertEqual(len(mock_client.synthesize_calls), 3)

    def test_19_duration_calculation(self):
        mock_client = MockPiperClient()
        tts = RealTTS(client=mock_client)
        tts.run(self.project)

        total_audio = self.project.data["tts"]["total_audio_duration"]
        self.assertAlmostEqual(total_audio, 3.0, places=1)

    def test_20_progress_events(self):
        events = []

        def mock_emit(event_type, stage, **kwargs):
            events.append({"event": event_type, "stage": stage, **kwargs})

        with patch("autodub.modules.tts.emit_event", side_effect=mock_emit):
            mock_client = MockPiperClient()
            tts = RealTTS(client=mock_client)
            tts.run(self.project)

        event_types = [e["event"] for e in events]
        self.assertIn("stage_start", event_types)
        self.assertIn("progress", event_types)
        self.assertIn("stage_complete", event_types)


if __name__ == "__main__":
    unittest.main()
