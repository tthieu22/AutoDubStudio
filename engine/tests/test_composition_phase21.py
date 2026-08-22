import unittest
from pathlib import Path
import tempfile
import shutil

from autodub.modules.composition import Composition, Layer


class TestCompositionPhase21(unittest.TestCase):

    def setUp(self):
        self.temp_dir = tempfile.mkdtemp(prefix="autodub_test_comp_")
        self.comp_file = Path(self.temp_dir) / "composition.json"

    def tearDown(self):
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_01_composition_creation_and_persistence(self):
        comp = Composition(width=1920, height=1080, fps=30.0)
        layer1 = Layer(
            id="title-1",
            type="title",
            text="AUTO DUB STUDIO",
            start=0.0,
            duration=5.0,
            x=960,
            y=100,
            z_index=1,
            style={"font_size": 50, "color": "yellow"}
        )
        comp.layers.append(layer1)
        comp.save(self.comp_file)

        self.assertTrue(self.comp_file.exists())
        loaded = Composition.load(self.comp_file)
        self.assertEqual(len(loaded.layers), 1)
        self.assertEqual(loaded.layers[0].id, "title-1")
        self.assertEqual(loaded.layers[0].text, "AUTO DUB STUDIO")

    def test_02_filtergraph_generation(self):
        comp = Composition()
        layer_text = Layer(
            id="text-1",
            type="text",
            text="Hello World",
            x=100,
            y=200,
            z_index=0
        )
        comp.layers.append(layer_text)

        filtergraph, extra_inputs = comp.build_ffmpeg_filtergraph(base_video_stream="[0:v]")
        self.assertIn("drawtext=text='Hello World':x=100:y=200", filtergraph)
        self.assertEqual(len(extra_inputs), 0)


if __name__ == "__main__":
    unittest.main()
