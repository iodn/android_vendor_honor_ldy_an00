# SPDX-License-Identifier: Apache-2.0
import json
from pathlib import Path
import re
import unittest

ROOT = Path(__file__).resolve().parents[1]

class InputInventoryTests(unittest.TestCase):
    def setUp(self):
        self.rows = json.loads((ROOT / "proprietary-inputs.json").read_text())["inputs"]
        self.inputs = {item["path"]: item for item in self.rows}

    def test_unique_valid_inputs_without_personal_authorization(self):
        self.assertEqual(len(self.inputs), len(self.rows))
        for path, item in self.inputs.items():
            self.assertTrue(path.startswith("proprietary/"))
            self.assertNotIn("..", Path(path).parts)
            self.assertFalse(path.startswith("proprietary/debug/"))
            self.assertGreater(item["size"], 0)
            self.assertRegex(item["sha256"], r"^[0-9a-f]{64}$")

    def test_every_declared_prebuilt_source_is_catalogued(self):
        paths = set(re.findall(r'"(proprietary/[^"]+)"', (ROOT / "Android.bp").read_text()))
        self.assertTrue(paths)
        self.assertEqual(paths - self.inputs.keys(), set())

    def test_tee_configuration_and_boot_metadata_agree(self):
        expected = []
        for item in json.loads((ROOT / "tee-framework-blobs.json").read_text()):
            expected.append((item["proprietary_path"], item["size"], item["sha256"]))
        for item in json.loads((ROOT / "tee-framework-configs.json").read_text())["entries"]:
            expected.append((item["proprietary_path"], item["bytes"], item["sha256"]))
        for item in json.loads((ROOT / "stock-images.json").read_text()):
            expected.append((item["file"], item["size"], item["sha256"]))
        for path, size, digest in expected:
            self.assertIn(path, self.inputs)
            self.assertEqual(self.inputs[path]["size"], size)
            self.assertEqual(self.inputs[path]["sha256"], digest)

if __name__ == "__main__":
    unittest.main()
