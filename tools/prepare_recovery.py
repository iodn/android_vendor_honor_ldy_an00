#!/usr/bin/env python3
# SPDX-License-Identifier: Apache-2.0
"""Stage the hash-pinned recovery HAL from an extracted stock vendor partition."""
import argparse
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def inventory(output_root):
    entries = json.loads((output_root / "recovery/blobs.json").read_text())["inputs"]
    expected = {
        "/vendor/bin/hw/android.hardware.boot-service.mtk":
            "recovery/blobs/vendor/bin/hw/android.hardware.boot-service.mtk",
        "/vendor/lib64/libmtk_bsg.so": "recovery/blobs/vendor/lib64/libmtk_bsg.so",
    }
    if len(entries) != 2 or {e["source"]: e["path"] for e in entries} != expected:
        raise ValueError("Unexpected recovery input inventory")
    return entries


def check(output_root=ROOT):
    entries = inventory(output_root)
    for entry in entries:
        staged = output_root / entry["path"]
        if not staged.is_file() or staged.is_symlink():
            raise ValueError("Recovery input missing or not a regular file: " + entry["path"])
        data = staged.read_bytes()
        if len(data) != entry["size"] or hashlib.sha256(data).hexdigest() != entry["sha256"]:
            raise ValueError("Recovery input mismatch: " + entry["path"])
    return len(entries)


def prepare(vendor_root, output_root=ROOT):
    entries = inventory(output_root)
    checked = []
    for entry in entries:
        source = vendor_root / entry["source"].removeprefix("/vendor/")
        data = source.read_bytes()
        if len(data) != entry["size"] or hashlib.sha256(data).hexdigest() != entry["sha256"]:
            raise ValueError("Recovery input mismatch: " + entry["source"])
        checked.append((data, output_root / entry["path"]))
    # Validate both files before changing either staged input.
    for data, destination in checked:
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_bytes(data)
    return len(checked)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    modes = parser.add_mutually_exclusive_group(required=True)
    modes.add_argument("--vendor-root", type=Path)
    modes.add_argument("--check", action="store_true", help="Validate staged inputs without writing")
    args = parser.parse_args()
    try:
        count = check() if args.check else prepare(args.vendor_root)
    except (OSError, ValueError) as error:
        parser.exit(1, "Recovery input check failed: " + str(error) +
                    "\nRun prepare_recovery.py --vendor-root /path/to/extracted/vendor before configuring either product.\n")
    print("RECOVERY_INPUTS_OK", count)
