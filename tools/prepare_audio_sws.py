#!/usr/bin/env python3
# SPDX-License-Identifier: Apache-2.0
"""Prepare pinned stock SWS inputs and deterministic tuning for a private vendor tree."""
import argparse, hashlib, json
from pathlib import Path
from pack_sws_tuning import pack
def prepare(vendor_root, product_root, odm_root):
    inventory=json.loads((vendor_root/'audio-sws-inputs.json').read_text())
    roots={'product':product_root,'odm':odm_root}
    staged=[]
    for item in inventory['inputs']:
        partition,relative=item['source'].lstrip('/').split('/',1)
        data=(roots[partition]/relative).read_bytes()
        if len(data)!=item['size'] or hashlib.sha256(data).hexdigest()!=item['sha256']:
            raise ValueError('Stock SWS input mismatch: '+item['source'])
        staged.append((item['proprietary_path'],data))
    generated=inventory['generated'];data=pack(odm_root/'etc/sws')
    if len(data)!=generated['size'] or hashlib.sha256(data).hexdigest()!=generated['sha256']:
        raise ValueError('Generated SWS tuning mismatch')
    staged.append((generated['proprietary_path'],data))
    # All source/generation checks finish before touching destination inputs.
    for relative,data in staged:
        destination=vendor_root/relative;destination.parent.mkdir(parents=True,exist_ok=True)
        destination.write_bytes(data)
    return len(staged)
if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--vendor-root',type=Path,default=Path(__file__).resolve().parents[1])
    parser.add_argument('--product-root',type=Path,required=True)
    parser.add_argument('--odm-root',type=Path,required=True)
    args=parser.parse_args();print('AUDIO_SWS_PREPARED',prepare(args.vendor_root,args.product_root,args.odm_root))
