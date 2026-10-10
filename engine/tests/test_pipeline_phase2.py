import json
import os
import shutil
import tempfile
import unittest
from pathlib import Path

from autodub.models.project import Project
from autodub.pipeline.state import PipelineStage, StageStatus, validate_state_transition, STAGE_ORDER
from autodub.pipeline.validator import ProjectValidator
from autodub.pipeline.manager import PipelineManager
from autodub.exceptions import (
    ProjectValidationError, StateTransitionError, StageDependencyError, PipelineCancelledError
)

class TestPhase2Pipeline(unittest.TestCase):
    def setUp(self):
        from unittest.mock import patch
        from tests.test_translator_phase5 import MockOllamaClient
        from tests.test_tts_phase6 import MockPiperClient
        self.patcher_ollama = patch('autodub.modules.translator.OllamaClient', MockOllamaClient)
        self.patcher_piper = patch('autodub.modules.tts.PiperClient', MockPiperClient)
        self.patcher_ollama.start()
        self.patcher_piper.start()

        self.test_dir = Path(tempfile.mkdtemp(prefix="autodub_test_"))
        self.project_dir = self.test_dir / "test_project"
        src_file = self.project_dir / "source" / "input.mp4"
        src_file.parent.mkdir(parents=True, exist_ok=True)
        # Create a small valid mp4 video for phase 2 tests
        from tests.test_extractor_phase3 import create_synthetic_media
        create_synthetic_media(src_file, has_audio=True, duration=2.0)

    def tearDown(self):
        self.patcher_piper.stop()
        self.patcher_ollama.stop()
        if self.test_dir.exists():
            shutil.rmtree(self.test_dir, ignore_errors=True)

    def test_01_create_and_load_project(self):
        proj = Project(self.project_dir, name="test_project")
        self.assertTrue((self.project_dir / "project.json").exists())
        self.assertEqual(proj.data["name"], "test_project")
        self.assertEqual(proj.data["version"], 1)
        self.assertIn("project_id", proj.data)

        # Reload
        proj2 = Project(self.project_dir)
        self.assertEqual(proj2.data["project_id"], proj.data["project_id"])

    def test_02_atomic_save_and_backup(self):
        proj = Project(self.project_dir, name="test_project")
        proj.update_stage("extract", StageStatus.COMPLETED.value, progress=100)
        
        bak_file = self.project_dir / "project.json.bak"
        proj.update_stage("transcribe", StageStatus.RUNNING.value, progress=50)
        
        self.assertTrue(bak_file.exists())
        with open(bak_file, "r", encoding="utf-8") as f:
            bak_data = json.load(f)
        self.assertEqual(bak_data["pipeline"]["extract"]["status"], "completed")

    def test_03_backup_recovery_on_corruption(self):
        proj = Project(self.project_dir, name="test_project")
        proj.update_stage("extract", StageStatus.COMPLETED.value)
        proj.save()  # Creates backup

        # Corrupt project.json
        with open(self.project_dir / "project.json", "w", encoding="utf-8") as f:
            f.write("{ INVALID JSON CORRUPTED FILE ")

        # Reloading should automatically recover from backup
        proj_recovered = Project(self.project_dir)
        self.assertEqual(proj_recovered.data["pipeline"]["extract"]["status"], "completed")

    def test_04_state_transitions(self):
        # Valid
        validate_state_transition(StageStatus.PENDING, StageStatus.RUNNING)
        validate_state_transition(StageStatus.RUNNING, StageStatus.COMPLETED)
        validate_state_transition(StageStatus.FAILED, StageStatus.RUNNING)
        validate_state_transition(StageStatus.CANCELLED, StageStatus.RUNNING)

        # Invalid
        with self.assertRaises(StateTransitionError):
            validate_state_transition(StageStatus.COMPLETED, StageStatus.RUNNING, force=False)
        
        # Valid with force
        validate_state_transition(StageStatus.COMPLETED, StageStatus.RUNNING, force=True)

    def test_05_dependency_validation(self):
        proj = Project(self.project_dir, name="test_project")
        # TRANSLATE set to COMPLETED while TRANSCRIBE is PENDING -> Invalid
        proj.data["pipeline"]["translate"]["status"] = StageStatus.COMPLETED.value
        proj.save()

        with self.assertRaises(ProjectValidationError):
            ProjectValidator.validate(proj)

    def test_06_acceptance_scenario_a_full_normal_run(self):
        mgr = PipelineManager(str(self.project_dir), step_delay=0.01)
        mgr.run_all()

        for stage in STAGE_ORDER:
            info = mgr.project.get_stage_info(stage.value)
            self.assertEqual(info["status"], StageStatus.COMPLETED.value)
            self.assertEqual(info["progress"], 100)

    def test_07_acceptance_scenario_b_crash_and_partial_resume(self):
        mgr = PipelineManager(str(self.project_dir), step_delay=0.01)
        
        # Simulate run that fails/crashes at TRANSLATE step 5 (50%)
        with self.assertRaises(RuntimeError):
            mgr.run_all(fail_at_stage=PipelineStage.TRANSLATE, fail_at_step=5)

        # Verify project state saved checkpoint at TRANSLATE step 4 (40%)
        translate_info = mgr.project.get_stage_info("translate")
        self.assertEqual(translate_info["status"], StageStatus.FAILED.value)
        self.assertEqual(translate_info["current"], 4)

        # Resume execution
        mgr_resume = PipelineManager(str(self.project_dir), step_delay=0.01)
        mgr_resume.resume()

        # Check all stages completed
        for stage in STAGE_ORDER:
            info = mgr_resume.project.get_stage_info(stage.value)
            self.assertEqual(info["status"], StageStatus.COMPLETED.value)

    def test_08_acceptance_scenario_c_stage_failed_and_retry(self):
        mgr = PipelineManager(str(self.project_dir), step_delay=0.01)
        
        # Simulate TTS fail
        with self.assertRaises(RuntimeError):
            mgr.run_all(fail_at_stage=PipelineStage.TTS, fail_at_step=3)

        # Verify TTS is FAILED, SYNC & RENDER remain PENDING
        self.assertEqual(mgr.project.get_stage_info("tts")["status"], StageStatus.FAILED.value)
        self.assertEqual(mgr.project.get_stage_info("sync")["status"], StageStatus.PENDING.value)
        self.assertEqual(mgr.project.get_stage_info("render")["status"], StageStatus.PENDING.value)

        # Retry TTS
        mgr_retry = PipelineManager(str(self.project_dir), step_delay=0.01)
        mgr_retry.retry(PipelineStage.TTS)

        # Verify all stages completed now
        for stage in STAGE_ORDER:
            self.assertEqual(mgr_retry.project.get_stage_info(stage.value)["status"], StageStatus.COMPLETED.value)

    def test_09_acceptance_scenario_d_render_failed_and_retry(self):
        mgr = PipelineManager(str(self.project_dir), step_delay=0.01)
        
        # Simulate RENDER fail
        with self.assertRaises(RuntimeError):
            mgr.run_all(fail_at_stage=PipelineStage.RENDER, fail_at_step=2)

        self.assertEqual(mgr.project.get_stage_info("sync")["status"], StageStatus.COMPLETED.value)
        self.assertEqual(mgr.project.get_stage_info("render")["status"], StageStatus.FAILED.value)

        # Retry RENDER only
        mgr_retry = PipelineManager(str(self.project_dir), step_delay=0.01)
        mgr_retry.retry(PipelineStage.RENDER)

        self.assertEqual(mgr_retry.project.get_stage_info("render")["status"], StageStatus.COMPLETED.value)

    def test_10_cancellation_and_resume(self):
        mgr = PipelineManager(str(self.project_dir), step_delay=0.01)
        mgr.cancel()  # Request cancel immediately

        with self.assertRaises(PipelineCancelledError):
            mgr.run_all()

        # Check stage status is CANCELLED
        extract_info = mgr.project.get_stage_info("extract")
        self.assertEqual(extract_info["status"], StageStatus.CANCELLED.value)

        # Reset cancel flag and resume
        mgr_resume = PipelineManager(str(self.project_dir), step_delay=0.01)
        mgr_resume.resume()
        
        for stage in STAGE_ORDER:
            self.assertEqual(mgr_resume.project.get_stage_info(stage.value)["status"], StageStatus.COMPLETED.value)

if __name__ == "__main__":
    unittest.main()
