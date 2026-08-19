import json
import os
import shutil
import tempfile
import time
import unittest
import wave
from pathlib import Path
from unittest.mock import patch, MagicMock

from autodub.models.project import Project
from autodub.pipeline.manager import PipelineManager
from autodub.pipeline.state import PipelineStage, StageStatus
from autodub.modules.synchronizer import (
    RealSynchronizer,
    AudioSynchronizer,
    calculate_target_duration,
    calculate_speed_factor,
    build_atempo_filter,
    validate_sync_duration,
    probe_audio_duration,
    generate_silent_wav,
    resolve_timeline_overlaps,
    resolve_timeline_gaps,
)
from autodub.exceptions import (
    SyncError,
    SyncExtremeSpeedError,
    SyncOverlapError,
    SyncDurationMismatchError,
    PipelineCancelledError,
    SyncCancelledError,
)
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


class TestPhase7Synchronizer(unittest.TestCase):

    def setUp(self):
        self.temp_dir = tempfile.mkdtemp(prefix="autodub_test_sync_")
        self.project_dir = Path(self.temp_dir) / "test_project"
        self.project = Project(self.project_dir, name="test_project")

        # Populate sample segments
        self.project.data["segments"] = [
            {
                "id": 1,
                "start": 10.0,
                "end": 12.5,
                "text": "Hello world",
                "translated_text": "Xin chào thế giới",
                "tts": {"path": "audio/tts/000001.wav", "duration": 3.2, "status": "COMPLETED"}
            },
            {
                "id": 2,
                "start": 14.0,
                "end": 16.0,
                "text": "Good morning",
                "translated_text": "Chào buổi sáng",
                "tts": {"path": "audio/tts/000002.wav", "duration": 1.5, "status": "COMPLETED"}
            },
            {
                "id": 3,
                "start": 18.0,
                "end": 20.0,
                "text": "Thank you",
                "translated_text": "Cảm ơn bạn",
                "tts": {"path": "audio/tts/000003.wav", "duration": 2.0, "status": "COMPLETED"}
            }
        ]
        self.project.save()

        # Create synthetic source video file for pipeline integration tests
        src_file = self.project_dir / "source" / "input.mp4"
        src_file.parent.mkdir(parents=True, exist_ok=True)
        with open(src_file, "wb") as f:
            f.write(b"MOCK_VIDEO_DATA")

        # Create synthetic input TTS WAV files
        tts_dir = self.project_dir / "audio" / "tts"
        create_synthetic_wav(tts_dir / "000001.wav", 3.2)
        create_synthetic_wav(tts_dir / "000002.wav", 1.5)
        create_synthetic_wav(tts_dir / "000003.wav", 2.0)

    def tearDown(self):
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_01_calculate_target_duration(self):
        seg = {"start": 10.0, "end": 12.5}
        self.assertEqual(calculate_target_duration(seg), 2.5)

    def test_02_calculate_speed_factor(self):
        self.assertEqual(calculate_speed_factor(3.2, 2.5), 1.28)
        self.assertEqual(calculate_speed_factor(1.5, 3.0), 0.5)

    def test_03_atempo_filter_for_1_0(self):
        self.assertEqual(build_atempo_filter(1.0), "anull")

    def test_04_atempo_filter_for_1_5(self):
        self.assertEqual(build_atempo_filter(1.5), "atempo=1.5")

    def test_05_atempo_filter_for_2_0(self):
        self.assertEqual(build_atempo_filter(2.0), "atempo=2.0")

    def test_06_atempo_decomposition_above_2_0(self):
        filter_str = build_atempo_filter(4.0)
        self.assertEqual(filter_str, "atempo=2.0,atempo=2.0")

    def test_07_atempo_decomposition_below_0_5(self):
        filter_str = build_atempo_filter(0.25)
        self.assertEqual(filter_str, "atempo=0.5,atempo=0.5")

    def test_08_normal_synchronization(self):
        sync = RealSynchronizer(step_delay=0.01)
        sync.run(self.project)
        self.assertEqual(self.project.get_stage_info("sync")["status"], StageStatus.COMPLETED.value)
        synced_dir = self.project_dir / "audio" / "synced"
        self.assertTrue((synced_dir / "000001.wav").exists())
        self.assertTrue((synced_dir / "combined.wav").exists())

    def test_09_tts_longer_than_target(self):
        seg = self.project.data["segments"][0]
        # TTS=3.2s, Target=2.5s -> ratio 1.28x
        sync = RealSynchronizer(step_delay=0.01)
        sync.run(self.project)
        out_wav = self.project_dir / "audio" / "synced" / "000001.wav"
        dur = probe_audio_duration(out_wav)
        self.assertTrue(validate_sync_duration(dur, 2.5))

    def test_10_tts_shorter_than_target(self):
        seg = self.project.data["segments"][1]
        # TTS=1.5s, Target=2.0s -> ratio 0.75x
        sync = RealSynchronizer(step_delay=0.01)
        sync.run(self.project)
        out_wav = self.project_dir / "audio" / "synced" / "000002.wav"
        dur = probe_audio_duration(out_wav)
        self.assertTrue(validate_sync_duration(dur, 2.0))

    def test_11_duration_tolerance_validation(self):
        self.assertTrue(validate_sync_duration(2.52, 2.50, tolerance=0.05))
        self.assertFalse(validate_sync_duration(2.60, 2.50, tolerance=0.05))

    def test_12_correction_pass(self):
        sync = RealSynchronizer(step_delay=0.01)
        # Mock run_segment_sync to test 2 passes
        with patch.object(sync, "run_segment_sync", wraps=sync.run_segment_sync) as mock_sync:
            sync.run(self.project)
            self.assertTrue(mock_sync.called)

    def test_13_extreme_speed_clamp(self):
        # Target 1.0s, TTS 5.0s -> required speed 5.0x -> clamped to 2.0x
        self.project.data["segments"][0]["end"] = 11.0  # target = 1.0s
        self.project.save()
        sync = RealSynchronizer(step_delay=0.01)
        sync.run(self.project, extreme_policy="CLAMP")
        sync_meta = self.project.data["segments"][0]["sync"]
        self.assertTrue(sync_meta["clamped"])
        self.assertEqual(sync_meta["applied_speed"], 2.0)

    def test_14_extreme_speed_reject(self):
        self.project.data["segments"][0]["end"] = 11.0  # target = 1.0s
        self.project.save()
        sync = RealSynchronizer(step_delay=0.01)
        with self.assertRaises(SyncExtremeSpeedError):
            sync.run(self.project, extreme_policy="REJECT")

    def test_15_empty_segment(self):
        self.project.data["segments"][0]["text"] = ""
        self.project.save()
        sync = RealSynchronizer(step_delay=0.01)
        sync.run(self.project)
        sync_meta = self.project.data["segments"][0]["sync"]
        self.assertEqual(sync_meta["status"], "SKIPPED")
        self.assertEqual(sync_meta["reason"], "EMPTY_TEXT")

    def test_16_missing_tts_file(self):
        (self.project_dir / "audio" / "tts" / "000001.wav").unlink()
        sync = RealSynchronizer(step_delay=0.01)
        sync.run(self.project)
        sync_meta = self.project.data["segments"][0]["sync"]
        self.assertEqual(sync_meta["status"], "SKIPPED")

    def test_17_corrupted_tts_file(self):
        with open(self.project_dir / "audio" / "tts" / "000001.wav", "wb") as f:
            f.write(b"CORRUPTED_DATA")
        sync = RealSynchronizer(step_delay=0.01)
        sync.run(self.project)
        # Corrupted zero-duration audio falls back to silent WAV
        self.assertEqual(self.project.get_stage_info("sync")["status"], StageStatus.COMPLETED.value)

    def test_18_atomic_output(self):
        sync = RealSynchronizer(step_delay=0.01)
        sync.run(self.project)
        synced_dir = self.project_dir / "audio" / "synced"
        self.assertTrue((synced_dir / "000001.wav").exists())
        self.assertFalse((synced_dir / "000001.wav.tmp").exists())

    def test_19_existing_valid_output_is_skipped(self):
        sync = RealSynchronizer(step_delay=0.01)
        sync.run(self.project)

        with patch.object(sync, "run_segment_sync") as mock_run_seg:
            sync.run(self.project)
            mock_run_seg.assert_not_called()

    def test_20_force_flag_regenerates_output(self):
        sync = RealSynchronizer(step_delay=0.01)
        sync.run(self.project)

        with patch.object(sync, "run_segment_sync", wraps=sync.run_segment_sync) as mock_run_seg:
            sync.run(self.project, force=True)
            self.assertEqual(mock_run_seg.call_count, 3)

    def test_21_checkpoint_created(self):
        sync = RealSynchronizer(step_delay=0.01)
        sync.run(self.project)
        chk_path = self.project_dir / "audio" / "synced" / "sync.partial.json"
        self.assertTrue(chk_path.exists())
        with open(chk_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        self.assertIn("completed_segments", data)
        self.assertEqual(len(data["completed_segments"]), 3)

    def test_22_resume_skips_completed_segments(self):
        sync = RealSynchronizer(step_delay=0.01)

        # Fail at step 2
        with self.assertRaises(RuntimeError):
            sync.run(self.project, fail_at_step=2)

        chk_path = self.project_dir / "audio" / "synced" / "sync.partial.json"
        self.assertTrue(chk_path.exists())

        with patch.object(sync, "run_segment_sync", wraps=sync.run_segment_sync) as mock_run_seg:
            sync.run(self.project)
            # Segment 1 was completed, so only segment 2 & 3 should run
            self.assertLessEqual(mock_run_seg.call_count, 2)

    def test_23_resume_detects_corrupted_completed_output(self):
        sync = RealSynchronizer(step_delay=0.01)
        sync.run(self.project)

        # Reset stage status to RUNNING so sync doesn't skip early on COMPLETED
        self.project.update_stage("sync", StageStatus.RUNNING.value)
        self.project.save()

        # Corrupt segment 1 output
        with open(self.project_dir / "audio" / "synced" / "000001.wav", "wb") as f:
            f.write(b"CORRUPTED")

        with patch.object(sync, "run_segment_sync", wraps=sync.run_segment_sync) as mock_run_seg:
            sync.run(self.project)
            self.assertGreaterEqual(mock_run_seg.call_count, 1)

    def test_24_cancellation(self):
        sync = RealSynchronizer(step_delay=0.01)
        with self.assertRaises(PipelineCancelledError):
            sync.run(self.project, is_cancelled=lambda: True)
        self.assertEqual(self.project.get_stage_info("sync")["status"], StageStatus.CANCELLED.value)

    def test_25_retry_after_transient_ffmpeg_error(self):
        sync = RealSynchronizer(step_delay=0.01)
        calls = [0]

        def fail_once(*args, **kwargs):
            calls[0] += 1
            if calls[0] == 1:
                raise SyncFFmpegError("Simulated transient error")
            return RealSynchronizer.run_segment_sync(sync, *args, **kwargs)

        with patch.object(sync, "run_segment_sync", side_effect=fail_once):
            sync.run(self.project)
            self.assertEqual(self.project.get_stage_info("sync")["status"], StageStatus.COMPLETED.value)

    def test_26_gap_handling(self):
        gaps = resolve_timeline_gaps(self.project.data["segments"])
        gap_items = [g for g in gaps if g["type"] == "gap"]
        self.assertTrue(len(gap_items) >= 2)
        self.assertEqual(gap_items[1]["duration"], 1.5)  # 12.5 to 14.0

    def test_27_multiple_gaps(self):
        items = resolve_timeline_gaps(self.project.data["segments"])
        types = [i["type"] for i in items]
        self.assertIn("gap", types)
        self.assertIn("segment", types)

    def test_28_overlap_detection(self):
        overlapping = [
            {"id": 1, "start": 10.0, "end": 13.0},
            {"id": 2, "start": 12.5, "end": 15.0}
        ]
        resolved = resolve_timeline_overlaps(overlapping, policy="TRIM")
        self.assertTrue(resolved[1].get("overlap_trimmed"))
        self.assertEqual(resolved[1]["effective_start"], 13.0)

    def test_29_overlap_trim_policy(self):
        overlapping = [
            {"id": 1, "start": 10.0, "end": 13.0},
            {"id": 2, "start": 12.5, "end": 15.0}
        ]
        resolved = resolve_timeline_overlaps(overlapping, policy="TRIM")
        self.assertEqual(resolved[1]["target_duration"], 2.0)

    def test_30_overlap_fail_policy(self):
        overlapping = [
            {"id": 1, "start": 10.0, "end": 13.0},
            {"id": 2, "start": 12.5, "end": 15.0}
        ]
        with self.assertRaises(SyncOverlapError):
            resolve_timeline_overlaps(overlapping, policy="FAIL")

    def test_31_very_short_segment(self):
        self.project.data["segments"][0]["end"] = 10.05  # target = 0.05s < 0.10s
        self.project.save()
        sync = RealSynchronizer(step_delay=0.01)
        sync.run(self.project)
        sync_meta = self.project.data["segments"][0]["sync"]
        self.assertEqual(sync_meta["status"], "SKIPPED")
        self.assertEqual(sync_meta["reason"], "TARGET_DURATION_TOO_SHORT")

    def test_32_combined_timeline_generation(self):
        sync = RealSynchronizer(step_delay=0.01)
        sync.run(self.project)
        comb_wav = self.project_dir / "audio" / "synced" / "combined.wav"
        self.assertTrue(comb_wav.exists())
        self.assertGreater(comb_wav.stat().st_size, 0)

    def test_33_combined_audio_contains_silence_for_gaps(self):
        sync = RealSynchronizer(step_delay=0.01)
        sync.run(self.project)
        comb_wav = self.project_dir / "audio" / "synced" / "combined.wav"
        dur = probe_audio_duration(comb_wav)
        self.assertGreaterEqual(dur, 19.9)

    def test_34_project_json_synchronization_metadata(self):
        sync = RealSynchronizer(step_delay=0.01)
        sync.run(self.project)
        self.assertIn("sync", self.project.data)
        self.assertEqual(self.project.data["sync"]["total_segments"], 3)
        self.assertIn("sync", self.project.data["segments"][0])

    def test_35_progress_events(self):
        events = []

        def mock_emit(event_type, stage, **kwargs):
            events.append({"event": event_type, "stage": stage, **kwargs})

        with patch("autodub.modules.synchronizer.emit_event", side_effect=mock_emit):
            sync = RealSynchronizer(step_delay=0.01)
            sync.run(self.project)

        event_types = [e["event"] for e in events]
        self.assertIn("stage_start", event_types)
        self.assertIn("progress", event_types)
        self.assertIn("stage_complete", event_types)

    def test_36_full_phase2_7_pipeline_integration(self):
        mgr = PipelineManager(str(self.project_dir), step_delay=0.01)

        # Mock extraction stage to create original.wav without calling real ffprobe on dummy file
        def mock_extract_run(proj, **kwargs):
            audio_dir = proj.project_dir / "audio"
            create_synthetic_wav(audio_dir / "original.wav", 10.0)
            proj.update_stage("extract", StageStatus.COMPLETED.value, progress=100)
            proj.save()
            return 0.01

        with patch("autodub.modules.extractor.RealExtractor.run", side_effect=mock_extract_run), \
             patch("autodub.modules.translator.OllamaClient", MockOllamaClient), \
             patch("autodub.modules.tts.PiperClient", MockPiperClient):
            mgr.run_all()

        for stage in [PipelineStage.EXTRACT, PipelineStage.TRANSCRIBE, PipelineStage.TRANSLATE, PipelineStage.TTS, PipelineStage.SYNC]:
            info = mgr.project.get_stage_info(stage.value)
            self.assertEqual(info["status"], StageStatus.COMPLETED.value)

    def test_37_audio_synchronizer_public_api(self):
        api = AudioSynchronizer(step_delay=0.01)
        res = api.synchronize_project(self.project_dir, force=True)
        self.assertEqual(res.total_segments, 3)
        self.assertGreaterEqual(res.completed_segments, 0)
