#!/usr/bin/env python3
# SPDX-License-Identifier: Apache-2.0
"""Verify exact stock NPU inputs before building the prebuilt modules."""
import argparse
import hashlib
import json
from pathlib import Path
import re
import subprocess

def verify(root):
    blobs = json.loads((root / "npu-framework-blobs.json").read_text())
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
