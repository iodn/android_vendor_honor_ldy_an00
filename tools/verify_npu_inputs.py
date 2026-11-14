#!/usr/bin/env python3
# SPDX-License-Identifier: Apache-2.0
"""Verify exact stock NPU inputs before building the prebuilt modules."""
import argparse
import hashlib
import json
from pathlib import Path
import re
import subprocess

PUBLIC_LIBRARIES = {
    "libneuronusdk_adapter.mtk.so", "libapuwareapusys_v2.mtk.so",
    "libapuwarehmp.mtk.so", "libapuwareutils.mtk.so",
    "libapuwareutils_v2.mtk.so", "libmvpu_engine_pub.mtk.so",
    "libmvpu_pattern_pub.mtk.so",
}


def verify_configuration(root):
    blobs = json.loads((root / "npu-framework-blobs.json").read_text())
    names = [item["module"] for item in blobs]
    paths = [item["proprietary_path"] for item in blobs]
    if len(blobs) != 14 or len(set(names)) != 14 or len(set(paths)) != 14:
        raise ValueError("NPU inventory must contain the complete 14-library cohort")

    public = (root / "config/npu/public.libraries-mtk.txt").read_text().splitlines()
    if len(public) != len(PUBLIC_LIBRARIES) or set(public) != PUBLIC_LIBRARIES:
        raise ValueError("NPU public library boundary differs from stock")

    blueprint = (root / "Android.bp").read_text()
    blocks = re.findall(r"cc_prebuilt_library_shared\s*\{.*?^\}", blueprint, re.S | re.M)
    selected = {}
    for block in blocks:
        match = re.search(r'\bname:\s*"(honor_npu_[^"]+)"', block)
        if match:
            if match[1] in selected:
                raise ValueError("Duplicate NPU prebuilt module")
            selected[match[1]] = block
    if set(selected) != set(names):
        raise ValueError("NPU build modules differ from the input inventory")
    for item in blobs:
        block = selected[item["module"]]
        sources = re.search(r"\bsrcs:\s*\[([^]]*)\]", block, re.S)
        stem = re.search(r'\bstem:\s*"([^"]+)"', block)
        expected = Path(item["source"]).name.removesuffix(".so")
        if (sources is None or re.findall(r'"([^"]+)"', sources[1]) != [item["proprietary_path"]]
                or stem is None or stem[1] != expected
                or item["destination_partition"] != "system_ext"
                or not re.search(r"\bsystem_ext_specific:\s*true\b", block)
                or not re.search(r'\bcompile_multilib:\s*"64"', block)):
            raise ValueError("NPU prebuilt path, partition or ABI mismatch: " + item["module"])

    makefile = "\n".join(line.split("#", 1)[0]
                         for line in (root / "npu-framework.mk").read_text().splitlines())
    packages = re.findall(r"\bhonor_npu_[A-Za-z0-9_]+\b",
                          makefile.split("PRODUCT_COPY_FILES", 1)[0])
    if len(packages) != 14 or set(packages) != set(names):
        raise ValueError("NPU product packages omit or duplicate a required library")
    public_copy = ("vendor/honor/ldy_an00/config/npu/public.libraries-mtk.txt:"
                   "$(TARGET_COPY_OUT_SYSTEM_EXT)/etc/public.libraries-mtk.txt")
    if makefile.count(public_copy) != 1:
        raise ValueError("NPU public library list must be installed in system_ext")
    return blobs


def verify(root):
    blobs = verify_configuration(root)
    for item in blobs:
        path = root / item["proprietary_path"]
        data = path.read_bytes()
        if len(data) != item["size"] or hashlib.sha256(data).hexdigest() != item["sha256"]:
            raise ValueError("NPU input mismatch: " + item["proprietary_path"])
    adapter = root / "proprietary/system_ext/lib64/libneuronusdk_adapter.mtk.so"
    if hashlib.sha256(adapter.read_bytes()).hexdigest() != "7d6a717154b29f511fa7af8808c086ca67b0fbc580707af7c015ab9ccb0c01f6":
        raise ValueError("The versioned-SONAME exception only permits the pinned stock adapter")
    result = subprocess.run(["readelf", "-d", str(adapter)], check=True, text=True, capture_output=True)
    names = re.findall(r"\(SONAME\).*?\[(.*?)\]", result.stdout)
    if names != ["libneuronusdk_adapter.mtk.so.8"]:
        raise ValueError("Unexpected stock adapter SONAME: " + repr(names))
    print("NPU_INPUTS_OK")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--vendor-root", type=Path, default=Path(__file__).resolve().parents[1])
    args = parser.parse_args()
    verify(args.vendor_root)
