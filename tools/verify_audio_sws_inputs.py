#!/usr/bin/env python3
# SPDX-License-Identifier: Apache-2.0
"""Verify exact stock SWS inputs and generated tuning before building prebuilts."""
import argparse, hashlib, json, re, subprocess
from pathlib import Path
def verify(root):
    inventory=json.loads((root/'audio-sws-inputs.json').read_text())
    entries=inventory['inputs']+[inventory['generated']]
    paths=[item['proprietary_path'] for item in entries]
    if len(paths)!=14 or len(set(paths))!=len(paths):raise ValueError('Invalid SWS inventory')
    for item in entries:
        path=root/item['proprietary_path'];data=path.read_bytes()
        if len(data)!=item['size'] or hashlib.sha256(data).hexdigest()!=item['sha256']:
            raise ValueError('SWS input mismatch: '+item['proprietary_path'])
    engine=root/'proprietary/product/lib64/lib64xisten7_3.so'
    dynamic=subprocess.run(['readelf','-d',str(engine)],check=True,text=True,capture_output=True).stdout
    if re.findall(r'\(SONAME\).*?\[(.*?)\]',dynamic)!=['lib64honorsound73.so']:
        raise ValueError('Unexpected stock SWS SONAME')
    return len(entries)
if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--vendor-root',type=Path,default=Path(__file__).resolve().parents[1])
    args=parser.parse_args();print('AUDIO_SWS_INPUTS_OK',verify(args.vendor_root))
