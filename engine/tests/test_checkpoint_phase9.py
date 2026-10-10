import json
import shutil
import tempfile
import unittest
from pathlib import Path

from autodub.models.project import Project
from autodub.jobs.job import Job
from autodub.orchestration.pipeline_context import PipelineContext
from autodub.orchestration.orchestrator import PipelineOrchestrator, STAGE_WEIGHTS


class TestPhase9CheckpointAndProgress(unittest.TestCase):

    def setUp(self):
        self.temp_dir = tempfile.mkdtemp(prefix="autodub_test_chk_")
        self.proj_dir = Path(self.temp_dir) / "test_project"
        self.project = Project(self.proj_dir, name="test_project")
        self.orchestrator = PipelineOrchestrator()

    def tearDown(self):
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_01_overall_progress_calculation(self):
        # 0 completed
        p0 = self.orchestrator.calculate_overall_progress([], "INGEST", 50.0)
        self.assertEqual(p0, 2.5)  # 50% of 5% INGEST = 2.5%

        # INGEST and TRANSCRIBE completed
        p2 = self.orchestrator.calculate_overall_progress(["INGEST", "TRANSCRIBE"], "TRANSLATE", 0.0)
        self.assertEqual(p2, 25.0)  # 5% + 20% = 25%

        # All completed
        all_stages = ["INGEST", "TRANSCRIBE", "TRANSLATE", "TTS", "SUBTITLE", "MIX", "RENDER", "VALIDATE"]
        p_all = self.orchestrator.calculate_overall_progress(all_stages, "VALIDATE", 100.0)
        self.assertEqual(p_all, 100.0)

    def test_02_checkpoint_save_and_load(self):
        job = Job.create(str(self.proj_dir), "in.mp4", "out.mp4", job_id="job_chk_1", config_hash="hash123")
        ctx = PipelineContext(job=job, project=self.project, config={}, workspace=self.proj_dir)

        completed = ["INGEST", "TRANSCRIBE"]
        self.orchestrator.save_checkpoint(ctx, completed, "TRANSLATE", "RUNNING")

        chk = self.orchestrator.load_checkpoint(ctx)
        self.assertEqual(chk["job_id"], "job_chk_1")
        self.assertEqual(chk["config_hash"], "hash123")
        self.assertEqual(chk["completed_stages"], ["INGEST", "TRANSCRIBE"])
        self.assertEqual(chk["current_stage"], "TRANSLATE")


if __name__ == "__main__":
    unittest.main()
