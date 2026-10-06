import tempfile
import unittest
from pathlib import Path

from PIL import Image, ImageDraw

from app.inference import DiseaseEngine


class SeverityProxyTests(unittest.TestCase):
    def setUp(self):
        self.engine = DiseaseEngine.__new__(DiseaseEngine)
        self.engine.input_size = 20
        self.temp_dir = tempfile.TemporaryDirectory()
        self.image_path = Path(self.temp_dir.name) / "leaf.png"

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_healthy_bright_green_leaf_has_no_lesion_ratio(self):
        Image.new("RGB", (20, 20), (145, 190, 70)).save(self.image_path)

        result = self.engine.severity_proxy(self.image_path)

        self.assertEqual(result["severity"], "healthy/very mild")
        self.assertEqual(result["lesion_ratio"], 0.0)

    def test_yellow_lesions_are_still_counted(self):
        image = Image.new("RGB", (20, 20), (145, 190, 70))
        ImageDraw.Draw(image).rectangle((0, 0, 9, 19), fill=(170, 175, 40))
        image.save(self.image_path)

        result = self.engine.severity_proxy(self.image_path)

        self.assertGreater(result["lesion_ratio"], 0.0)


if __name__ == "__main__":
    unittest.main()