# SPDX-License-Identifier: Apache-2.0
import hashlib
import json
from pathlib import Path
import tempfile
import unittest

from prepare_recovery import prepare, check, ROOT


class RecoveryInputsTest(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.vendor = self.root / "vendor"
        self.output = self.root / "output"
        (self.output / "recovery").mkdir(parents=True)
        self.inventory = json.loads((ROOT / "recovery/blobs.json").read_text())
        for index, item in enumerate(self.inventory["inputs"]):
            data = b"recovery fixture " + bytes([index])
            path = self.vendor / item["source"].removeprefix("/vendor/")
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(data)
            item["size"] = len(data)
            item["sha256"] = hashlib.sha256(data).hexdigest()
        self.save()

    def save(self):
        (self.output / "recovery/blobs.json").write_text(json.dumps(self.inventory))

    def test_pinned_files_staged_exactly(self):
        self.assertEqual(prepare(self.vendor, self.output), 2)
        for item in self.inventory["inputs"]:
            self.assertEqual((self.output / item["path"]).read_bytes(),
                             (self.vendor / item["source"].removeprefix("/vendor/")).read_bytes())

    def test_corruption_refuses_without_partial_staging(self):
        item = self.inventory["inputs"][1]
        source = self.vendor / item["source"].removeprefix("/vendor/")
        source.write_bytes(source.read_bytes()[:-1] + b"x")
        with self.assertRaisesRegex(ValueError, "mismatch"):
            prepare(self.vendor, self.output)
        self.assertFalse((self.output / "recovery/blobs").exists())

    def test_missing_input_refuses_without_partial_staging(self):
        item = self.inventory["inputs"][1]
        (self.vendor / item["source"].removeprefix("/vendor/")).unlink()
        with self.assertRaises(FileNotFoundError):
            prepare(self.vendor, self.output)
        self.assertFalse((self.output / "recovery/blobs").exists())

    def test_inventory_cannot_redirect_destination(self):
        self.inventory["inputs"][0]["path"] = "../outside"
        self.save()
        with self.assertRaisesRegex(ValueError, "inventory"):
            prepare(self.vendor, self.output)

    def test_readonly_check_accepts_prepared_files_without_changes(self):
        prepare(self.vendor, self.output)
        before = {item["path"]: (self.output / item["path"]).stat().st_mtime_ns
                  for item in self.inventory["inputs"]}
        self.assertEqual(check(self.output), 2)
        self.assertEqual(before, {item["path"]: (self.output / item["path"]).stat().st_mtime_ns
                                  for item in self.inventory["inputs"]})

    def test_readonly_check_rejects_missing_files(self):
        with self.assertRaisesRegex(ValueError, "missing"):
            check(self.output)
        self.assertFalse((self.output / "recovery/blobs").exists())

    def test_readonly_check_rejects_corruption_without_repairing_it(self):
        prepare(self.vendor, self.output)
        target = self.output / self.inventory["inputs"][1]["path"]
        target.write_bytes(b"corrupt")
        with self.assertRaisesRegex(ValueError, "mismatch"):
            check(self.output)
        self.assertEqual(target.read_bytes(), b"corrupt")

    def test_inventory_matches_build_inputs(self):
        blueprint = (ROOT / "recovery/Android.bp").read_text()
        for item in json.loads((ROOT / "recovery/blobs.json").read_text())["inputs"]:
            self.assertIn('"' + item["path"].removeprefix("recovery/") + '"', blueprint)
            self.assertIn('name: "' + item["module"] + '"', blueprint)
        self.assertNotIn("recovery/recovery.mk", (ROOT / "tee-framework.mk").read_text())


if __name__ == "__main__":
    unittest.main()
