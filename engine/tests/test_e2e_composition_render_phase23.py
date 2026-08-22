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
from tests.test_render_integration_phase8 import create_synthetic_wav, create_sample_srt


class TestPhase23CompositionE2E(unittest.TestCase):

    def setUp(self):
        self.temp_dir = tempfile.mkdtemp(prefix="autodub_test_comp_e2e_")
        self.project_dir = Path(self.temp_dir) / "test_comp_project"
        self.project = Project(self.project_dir, name="Composition E2E Test")

        self.project.data["segments"] = [
            {"id": 1, "start": 0.0, "end": 2.5, "text": "Hello", "translated_text": "Xin chào", "sync": {"status": "COMPLETED", "path": "audio/synced/000001.wav"}},
        ]
        for stage in ["extract", "transcribe", "translate", "tts", "sync"]:
            self.project.update_stage(stage, "completed", progress=100)

        self.project.save()

        synced_dir = self.project_dir / "audio" / "synced"
        create_synthetic_wav(synced_dir / "000001.wav", 2.5)

        create_sample_srt(self.project_dir / "transcript" / "translated.srt")

        src_video = self.project_dir / "source" / "input.mp4"
        src_video.parent.mkdir(parents=True, exist_ok=True)
        with open(src_video, "wb") as f:
            f.write(b"MOCK_VIDEO_DATA")

        # Create composition.json
        comp = Composition(width=1920, height=1080, fps=30.0)
        layer = Layer(
            id="title-1",
            type="title",
            text="AUTO DUB STUDIO",
            start=0.0,
            duration=5.0,
            x=800,
            y=100,
            z_index=1,
            style={"font_size": 40, "color": "yellow"}
        )
        comp.layers.append(layer)
        comp.save(self.project_dir / "composition.json")

    def tearDown(self):
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_01_render_with_composition_layer_overlay(self):
        renderer = RealRenderer(step_delay=0.01)

        def mock_mix(*args, **kwargs):
            return self.project_dir / "audio" / "mixed_audio.wav"

        def mock_exec(cmd, *args, **kwargs):
            # Verify filtergraph argument in FFmpeg command
            cmd_str = " ".join(cmd)
            self.assertIn("-vf", cmd)
            self.assertIn("drawtext=text='AUTO DUB STUDIO'", cmd_str)
            out_file = self.project_dir / "output" / ".final.mp4.tmp"
            with open(out_file, "wb") as f:
                f.write(b"MOCK_COMPOSITE_MP4_DATA")

        mock_probe = {
            "format": {"duration": "5.0"},
            "streams": [{"codec_type": "video", "width": 1920, "height": 1080, "r_frame_rate": "30/1"}]
        }

        with patch.object(renderer.mixer, "mix_project_audio", side_effect=mock_mix), \
             patch.object(renderer, "_execute_ffmpeg_with_progress", side_effect=mock_exec), \
             patch("autodub.modules.renderer.validate_rendered_output", return_value=mock_probe), \
             patch.object(renderer.runner, "probe", return_value=mock_probe):

            cfg = RenderConfig(subtitle_mode="NONE")
            elapsed = renderer.run(self.project, force=True, render_config=cfg)
            self.assertTrue((self.project_dir / "output" / "final.mp4").exists())
            self.assertEqual(self.project.get_stage_info("render")["status"], "completed")


if __name__ == "__main__":
    unittest.main()
