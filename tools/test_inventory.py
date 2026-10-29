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

    def test_npu_inventory_and_public_boundary(self):
        blobs = json.loads((ROOT / "npu-framework-blobs.json").read_text())
        self.assertEqual(len(blobs), 14)
        public = set((ROOT / "config/npu/public.libraries-mtk.txt").read_text().splitlines())
        self.assertEqual(len(public), 7)
        for item in blobs:
            entry = self.inputs[item["proprietary_path"]]
            self.assertEqual(entry["size"], item["size"])
            self.assertEqual(entry["sha256"], item["sha256"])
            self.assertEqual(item["destination_partition"], "system_ext")
            if Path(item["source"]).name in public:
                self.assertTrue(Path(item["source"]).name.endswith(".mtk.so"))
        self.assertEqual(public - {Path(item["source"]).name for item in blobs}, set())
        self.assertFalse(any(name.startswith("vendor.") for name in public))

    def test_audio_sws_inventory_matches_catalogue(self):
        inventory = json.loads((ROOT / "audio-sws-inputs.json").read_text())
        entries = inventory["inputs"] + [inventory["generated"]]
        self.assertEqual(len(entries), 14)
        self.assertEqual(len({item["proprietary_path"] for item in entries}), 14)
        for item in entries:
            entry = self.inputs[item["proprietary_path"]]
            self.assertEqual(entry["size"], item["size"])
            self.assertEqual(entry["sha256"], item["sha256"])
        self.assertEqual(inventory["engine_soname"], "lib64honorsound73.so")

    def test_npu_soname_exception_is_exact(self):
        text = (ROOT / "Android.bp").read_text()
        blocks = re.findall(r"cc_prebuilt_library_shared\s*\{.*?\n\}", text, re.S)
        npu = [block for block in blocks if 'name: "honor_npu_' in block]
        self.assertEqual(len(npu), 14)
        exceptions = [block for block in npu if "check_elf_files: false" in block]
        self.assertEqual(len(exceptions), 1)
        self.assertIn('name: "honor_npu_libneuronusdk_adapter_mtk"', exceptions[0])
        entry = self.inputs["proprietary/system_ext/lib64/libneuronusdk_adapter.mtk.so"]
        self.assertEqual(entry["sha256"], "7d6a717154b29f511fa7af8808c086ca67b0fbc580707af7c015ab9ccb0c01f6")

if __name__ == "__main__":
    unittest.main()
