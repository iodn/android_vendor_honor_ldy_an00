#!/usr/bin/env python3
"""Deterministic pinned stock SWS tuning extraction. No native addresses or goldens."""
import argparse, hashlib, json, struct, xml.etree.ElementTree as ET
from pathlib import Path
PINS = {'sws_config.xml': '28d1dbdc639d5112e9267545ba28d4aea8ce73792ee2f815117f3063480dbf43', 'sws_config_vmap.xml': 'ca723638a6a58450965694bbd02dae9575b340b844c4c486bae2117c99ff867f', 'spaConfig.bin': '5a514090bb3a54198465fb978b8a6369a1ade9f684b44ee7d8eb250a238bdeaf', 'sdcConfig.bin': 'c43db77a74abd513c865fff73b8f85fca8911572d234194c0f7b0836410add10', 'lph_config.bin': '89b7bf48372dd657ad6c8cceeb138d8a6d2e72923b3ee7d431339c5c20daabb6', 'tws_config1.bin': '8bc56ec58a3759c9c0571e8d7148c816f237e0e4c7ac7aa52c6345f3e39488da', 'tws_config2.bin': 'e049313921886e78eaa873a4cb641a80bb1670082464f5e68ff678651703885a', 'sur_config.bin': 'b854e9a5a7908bdcd4e4b8fbb1b56003c51a6cf0fbe52396b0fe1f04f1ea506b', 'teh_config.bin': '8b76fe27a58a6621c9aa3cdf8d7079fe3f8d01a77d6c047d5d236bff85330c18', 'ascconfig1.bin': 'f99ee076d6a0137f69297c66346879f60666c996a36e394b30f415e6aeb40bd4', 'ascconfig2.bin': 'ab78240f74d36008f69aa96eadd9bf034210aa3c95ef9c347eac3f6e77c21f25', 'actconfig1.bin': 'bb4856d37c67170b8c31b8d2a0fefd7920ef16c1301b68f00368dcda4af3f1d0'}
NAMES = list(PINS)[2:]
SIZES = [22572,24630,82120,131360,131360,5120,19200,4106,8210,1200]
def pack(source):
    raw = {}
    for name, digest in PINS.items():
        value = (source/name).read_bytes()
        if hashlib.sha256(value).hexdigest() != digest: raise ValueError("source hash: "+name)
        raw[name] = value
    records = {}
    for node in ET.fromstring(raw["sws_config.xml"]).iter("NV"):
        key = int(node.attrib["ID"])
        if key in records: raise ValueError("duplicate NV")
        values = [int(x,16) for x in node.attrib["PARAM_VALUE"].strip("{}").split(",")]
        records[key] = struct.pack("<"+"H"*len(values), *values)
    if len(records) != 285: raise ValueError("NV count")
    if records[30160] != struct.pack("<37H",0,*([1,4,7,10,13,15]*6)):
        raise ValueError("threshold contract")
    base = {k:v for k,v in records.items() if k%2 and len(v)==838}
    ext = {k:v for k,v in records.items() if not k%2 and len(v)==2552}
    if len(base)!=141 or len(ext)!=141: raise ValueError("record counts")
    rows = {}; duplicate = []
    for node in ET.fromstring(raw["sws_config_vmap.xml"]).iter("NV"):
        key = int(node.attrib["NUMID"]); value = (int(node.attrib["ID"]),int(node.attrib["EXTID"]))
        if key in rows:
            duplicate.append((key, rows[key], value))
        rows.setdefault(key, value)
    # Native parser equality branch preserves the first inserted payload.
    if duplicate != [(41626,(30209,30210),(30225,30226))]: raise ValueError("vmap duplicates changed")
    if len(rows)!=377 or any(b not in base or e not in ext for b,e in rows.values()):
        raise ValueError("row references")
    hp = records[30181] + records[30182][:64]
    if len(hp)!=576: raise ValueError("headphone table")
    out = bytearray(b"SWS0730B"+struct.pack("<6I",1,141,141,377,576,10))
    for group in (base,ext):
        for key,value in sorted(group.items()): out += struct.pack("<I",key)+value
    for key,(b,e) in sorted(rows.items()): out += struct.pack("<3I",key,b,e)
    out += hp
    for index,(name,size) in enumerate(zip(NAMES,SIZES)):
        if len(raw[name])!=size: raise ValueError("blob length")
        out += struct.pack("<2I",index,size)+raw[name]
    return bytes(out)
if __name__=="__main__":
    p=argparse.ArgumentParser();p.add_argument("source",type=Path);p.add_argument("output",type=Path)
    a=p.parse_args();data=pack(a.source);a.output.write_bytes(data)
    print(json.dumps({"bytes":len(data),"sha256":hashlib.sha256(data).hexdigest(),
      "scope":"Pinned stock tuning; duplicate41626 preserves the first entry, matching the stock parser."}))
