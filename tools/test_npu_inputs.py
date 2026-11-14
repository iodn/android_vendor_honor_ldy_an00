# SPDX-License-Identifier: Apache-2.0
"""Validate NPU packaging boundaries without proprietary blobs or an Android build."""
import importlib.util
import json
from pathlib import Path
import shutil
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("verify_npu_inputs", ROOT / "tools/verify_npu_inputs.py")
VERIFY = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(VERIFY)


class NpuConfigurationTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)
        for name in ["Android.bp", "npu-framework.mk", "npu-framework-blobs.json",
                     "config/npu/public.libraries-mtk.txt"]:
            target = self.root / name
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(ROOT / name, target)

    def change(self, name, old, new):
        path = self.root / name
        source = path.read_text()
        start = source.index('name: "honor_npu_') if name == "Android.bp" else 0
        self.assertIn(old, source[start:])
        path.write_text(source[:start] + source[start:].replace(old, new, 1))

    def rejected(self, reason):
        with self.assertRaisesRegex(ValueError, reason):
            VERIFY.verify_configuration(self.root)

    def test_complete_cohort(self):
        self.assertEqual(len(VERIFY.verify_configuration(self.root)), 14)

    def test_incomplete_inventory(self):
        path = self.root / "npu-framework-blobs.json"
        path.write_text(json.dumps(json.loads(path.read_text())[:1]))
        self.rejected("complete 14-library cohort")

    def test_duplicate_inventory_entry(self):
        path = self.root / "npu-framework-blobs.json"
        rows = json.loads(path.read_text())
        rows[-1] = rows[0]
        path.write_text(json.dumps(rows))
        self.rejected("complete 14-library cohort")

    def test_missing_product_package(self):
        self.change("npu-framework.mk", "    honor_npu_libapuwarehmp_mtk \\\n", "")
        self.rejected("product packages")

    def test_public_list_installation_missing(self):
        self.change("npu-framework.mk", "$(TARGET_COPY_OUT_SYSTEM_EXT)/etc/public.libraries-mtk.txt",
                    "$(TARGET_COPY_OUT_VENDOR)/etc/public.libraries-mtk.txt")
        self.rejected("public library list")

    def test_duplicate_product_package(self):
        self.change("npu-framework.mk", "honor_npu_libapuwarehmp_mtk",
                    "honor_npu_libapuwareutils_mtk")
        self.rejected("product packages")

    def test_private_interface_is_not_public(self):
        self.change("config/npu/public.libraries-mtk.txt", "libapuwarehmp.mtk.so",
                    "vendor.mediatek.hardware.apuware.hmp@1.0.so")
        self.rejected("public library boundary")

    def test_missing_public_backend(self):
        self.change("config/npu/public.libraries-mtk.txt", "libapuwarehmp.mtk.so\n", "")
        self.rejected("public library boundary")

    def test_duplicate_public_backend(self):
        self.change("config/npu/public.libraries-mtk.txt", "libapuwarehmp.mtk.so",
                    "libapuwareutils.mtk.so")
        self.rejected("public library boundary")

    def test_missing_prebuilt(self):
        self.change("Android.bp", 'name: "honor_npu_libapuwarehmp_mtk"',
                    'name: "removed_npu_libapuwarehmp_mtk"')
        self.rejected("build modules")

    def test_wrong_prebuilt_source(self):
        self.change("Android.bp", 'srcs: ["proprietary/system_ext/lib64/libapuwarehmp.mtk.so"]',
                    'srcs: ["proprietary/system_ext/lib64/libapuwareutils.mtk.so"]')
        self.rejected("path, partition or ABI mismatch")

    def test_wrong_prebuilt_stem(self):
        self.change("Android.bp", 'stem: "libapuwarehmp.mtk"', 'stem: "libapuwarehmp"')
        self.rejected("path, partition or ABI mismatch")

    def test_wrong_partition(self):
        self.change("Android.bp", "system_ext_specific: true", "vendor: true")
        self.rejected("path, partition or ABI mismatch")

    def test_wrong_abi(self):
        self.change("Android.bp", 'compile_multilib: "64"', 'compile_multilib: "32"')
        self.rejected("path, partition or ABI mismatch")


if __name__ == "__main__":
    unittest.main()
