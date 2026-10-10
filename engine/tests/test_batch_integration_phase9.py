import json
import os
import shutil
import tempfile
import time
import unittest
import wave
from pathlib import Path

from autodub.jobs.job_manager import JobManager
from autodub.jobs.job import Job
from autodub.jobs.job_state import JobState
from autodub.workers.worker_pool import WorkerPool
from autodub.models.project import Project
from autodub.orchestration.orchestrator import PipelineOrchestrator
from autodub.orchestration.pipeline_context import PipelineContext


def create_synthetic_wav(path: Path, duration: float = 2.0):
    path.parent.mkdir(parents=True, exist_ok=True)
    num_frames = int(duration * 16000)
    with wave.open(str(path), "wb") as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(16000)
        wf.writeframes(b"\x10\x00" * num_frames)


class TestPhase9BatchIntegration(unittest.TestCase):

    def setUp(self):
        self.temp_dir = tempfile.mkdtemp(prefix="autodub_test_batch_")
        self.db_path = Path(self.temp_dir) / "batch_jobs.db"
        self.lock_dir = Path(self.temp_dir) / "locks"
        self.job_mgr = JobManager(db_path=self.db_path, lock_dir=self.lock_dir)

    def tearDown(self):
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_01_batch_multi_job_pipeline_orchestration(self):
        # Create 3 synthetic video project environments
        jobs = []
        for i in range(1, 4):
            p_dir = Path(self.temp_dir) / f"batch_proj_{i}"
            project = Project(p_dir, name=f"batch_proj_{i}")

            # Create synthetic input video file
            src_file = p_dir / "source" / "input.mp4"
            src_file.parent.mkdir(parents=True, exist_ok=True)
            src_file.write_bytes(b"MOCK_VIDEO_DATA")

            # Create synthetic transcripts & audio files
            (p_dir / "transcript").mkdir(parents=True, exist_ok=True)
            create_synthetic_wav(p_dir / "audio" / "original.wav", 2.0)
            with open(p_dir / "transcript" / "original.srt", "w", encoding="utf-8") as f:
                f.write("1\n00:00:00,000 --> 00:00:02,000\nHello World\n\n")
            with open(p_dir / "transcript" / "translated.srt", "w", encoding="utf-8") as f:
                f.write("1\n00:00:00,000 --> 00:00:02,000\nXin chào thế giới\n\n")

            synced_dir = p_dir / "audio" / "synced"
            create_synthetic_wav(synced_dir / "combined.wav", 2.0)
            create_synthetic_wav(p_dir / "audio" / "mixed_audio.wav", 2.0)

            out_dir = p_dir / "output"
            out_dir.mkdir(parents=True, exist_ok=True)
            (out_dir / "final.mp4").write_bytes(b"MOCK_FINAL_MP4")

            job = self.job_mgr.create_job(
                project_id=str(p_dir),
                input_path=str(src_file),
                output_path=str(out_dir / "final.mp4"),
                job_id=f"job_batch_{i}",
                priority=i,
                auto_enqueue=True
            )
            jobs.append(job)

        self.assertEqual(self.job_mgr.queue.get_queue_length(), 3)

        # Run WorkerPool with 2 workers to process the batch
        pool = WorkerPool(job_manager=self.job_mgr, max_workers=2)
        pool.start()

        # Wait for processing to complete
        start_t = time.time()
        while time.time() - start_t < 15.0:
            completed_count = sum(
                1 for j_id in ["job_batch_1", "job_batch_2", "job_batch_3"]
                if self.job_mgr.get_job(j_id) and self.job_mgr.get_job(j_id).status == JobState.COMPLETED.value
            )
            if completed_count == 3:
                break
            time.sleep(0.1)

        pool.stop()

        # Verify all jobs completed
        for i in range(1, 4):
            j = self.job_mgr.get_job(f"job_batch_{i}")
            print(f"DEBUG: job_batch_{i} -> status={j.status if j else 'NONE'}, stage={j.current_stage if j else 'NONE'}, err={j.error_message if j else 'NONE'}")
            self.assertIsNotNone(j)
            self.assertEqual(j.status, JobState.COMPLETED.value)
            self.assertEqual(j.progress, 100.0)

            # Verify pipeline partial checkpoint created
            chk_file = Path(j.project_id) / "output" / "pipeline.partial.json"
            self.assertTrue(chk_file.exists())
            with open(chk_file, "r", encoding="utf-8") as f:
                cdata = json.load(f)
            self.assertEqual(cdata["status"], JobState.COMPLETED.value)

    def test_02_restart_skips_completed_stages(self):
        p_dir = Path(self.temp_dir) / "proj_restart"
        project = Project(p_dir, name="proj_restart")

        src_file = p_dir / "source" / "input.mp4"
        src_file.parent.mkdir(parents=True, exist_ok=True)
        src_file.write_bytes(b"MOCK_VIDEO")

        (p_dir / "transcript").mkdir(parents=True, exist_ok=True)
        create_synthetic_wav(p_dir / "audio" / "original.wav", 2.0)
        with open(p_dir / "transcript" / "original.srt", "w", encoding="utf-8") as f:
            f.write("1\n00:00:00,000 --> 00:00:02,000\nHello\n\n")
        with open(p_dir / "transcript" / "translated.srt", "w", encoding="utf-8") as f:
            f.write("1\n00:00:00,000 --> 00:00:02,000\nXin chào\n\n")

        create_synthetic_wav(p_dir / "audio" / "synced" / "combined.wav", 2.0)
        create_synthetic_wav(p_dir / "audio" / "mixed_audio.wav", 2.0)
        (p_dir / "output").mkdir(parents=True, exist_ok=True)
        (p_dir / "output" / "final.mp4").write_bytes(b"MOCK_MP4")

        job = self.job_mgr.create_job(
            project_id=str(p_dir),
            input_path=str(src_file),
            output_path=str(p_dir / "output" / "final.mp4"),
            job_id="job_restart"
        )

        orch = PipelineOrchestrator()
        ctx = PipelineContext(job=job, project=project, config={}, workspace=p_dir)

        # First run
        orch.run_pipeline(ctx)
        self.assertEqual(job.status, JobState.COMPLETED.value)

        # Second run should skip all valid cached stages
        skipped_events = []
        def cb(evt):
            if "skipped" in evt.get("message", "").lower():
                skipped_events.append(evt)
        ctx.progress_callback = cb

        orch.run_pipeline(ctx)
        self.assertGreater(len(skipped_events), 0)


if __name__ == "__main__":
    unittest.main()
