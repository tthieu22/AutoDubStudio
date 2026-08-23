import json
import shutil
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from autodub.models.project import Project
from autodub.modules.composition import Composition, Layer
from autodub.modules.render_config import RenderConfig
from autodub.modules.renderer import RealRenderer
from autodub.pipeline.manager import PipelineManager
from tests.test_render_integration_phase8 import create_synthetic_wav, create_sample_srt


class TestPhase11To20MasterE2E(unittest.TestCase):

    def setUp(self):
        self.temp_dir = tempfile.mkdtemp(prefix="autodub_master_11_20_")
        self.project_dir = Path(self.temp_dir) / "master_test_project"
        self.project = Project(self.project_dir, name="Master 10 Phase E2E Project")

        # Phase 11: Project & Workspace structure
        self.project.data["source"] = {"path": "source/input.mp4", "language": "en"}
        self.project.data["target"] = {"language": "vi"}
        self.project.data["segments"] = [
            {
                "id": 1,
                "start": 0.0,
                "end": 3.0,
                "text": "Welcome to AutoDub Studio",
                "translated_text": "Chào mừng đến với AutoDub Studio",
                "speaker": "Speaker 1",
                "sync": {"status": "COMPLETED", "path": "audio/synced/000001.wav"}
            }
        ]

        # Complete stages up to sync
        for st in ["extract", "transcribe", "translate", "tts", "sync"]:
            self.project.update_stage(st, "completed", progress=100)

        self.project.save()

        # Create assets
        synced_dir = self.project_dir / "audio" / "synced"
        create_synthetic_wav(synced_dir / "000001.wav", 3.0)
        create_sample_srt(self.project_dir / "transcript" / "translated.srt")

        src_video = self.project_dir / "source" / "input.mp4"
        src_video.parent.mkdir(parents=True, exist_ok=True)
        with open(src_video, "wb") as f:
            f.write(b"MOCK_MASTER_VIDEO")

        # Phase 13 & 16 & 18: Layer / Composition Engine with Fade In/Out transitions
        comp = Composition(width=1920, height=1080, fps=30.0, duration=10.0)
        layer_title = Layer(
            id="title-main",
            type="title",
            text="AUTODUB STUDIO PRO",
            start=0.0,
            duration=5.0,
            x=600,
            y=150,
            fade_in_sec=0.5,
            fade_out_sec=0.5,
            z_index=2,
            style={"font_size": 44, "color": "#facc15"}
        )
        layer_watermark = Layer(
            id="watermark-logo",
            type="logo",
            text="LOGO WATERMARK",
            start=0.0,
            duration=10.0,
            x=1600,
            y=80,
            opacity=0.8,
            z_index=3,
            style={"font_size": 24, "color": "#38bdf8"}
        )
        comp.layers.extend([layer_title, layer_watermark])
        comp.save(self.project_dir / "composition.json")

    def tearDown(self):
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_master_pipeline_execution_phases_11_to_20(self):
        # Verify Phase 11 & 13 Persistence
        self.assertTrue((self.project_dir / "project.json").exists())
        self.assertTrue((self.project_dir / "composition.json").exists())

        loaded_comp = Composition.load(self.project_dir / "composition.json")
        self.assertEqual(len(loaded_comp.layers), 2)
        self.assertEqual(loaded_comp.layers[0].fade_in_sec, 0.5)

        # Phase 19: Composition -> FFmpeg Render Engine
        renderer = RealRenderer(step_delay=0.01)

        def mock_mix(*args, **kwargs):
            return self.project_dir / "audio" / "mixed_audio.wav"

        def mock_exec(cmd, *args, **kwargs):
            cmd_str = " ".join(cmd)
            self.assertIn("-filter_complex", cmd)
            self.assertIn("AUTODUB STUDIO PRO", cmd_str)
            self.assertIn("LOGO WATERMARK", cmd_str)
            out_file = self.project_dir / "output" / ".final.mp4.tmp"
            with open(out_file, "wb") as f:
                f.write(b"MOCK_MASTER_OUTPUT_MP4")

        mock_probe = {
            "format": {"duration": "10.0"},
            "streams": [{"codec_type": "video", "width": 1920, "height": 1080, "r_frame_rate": "30/1"}]
        }

        with patch.object(renderer.mixer, "mix_project_audio", side_effect=mock_mix), \
             patch.object(renderer, "_execute_ffmpeg_with_progress", side_effect=mock_exec), \
             patch("autodub.modules.renderer.validate_rendered_output", return_value=mock_probe), \
             patch.object(renderer.runner, "probe", return_value=mock_probe):

            cfg = RenderConfig(video_codec="H264", encoder="CPU", subtitle_mode="NONE")
            elapsed = renderer.run(self.project, force=True, render_config=cfg)

            # Phase 20 Verification
            self.assertTrue((self.project_dir / "output" / "final.mp4").exists())
            self.assertEqual(self.project.get_stage_info("render")["status"], "completed")


if __name__ == "__main__":
    unittest.main()
