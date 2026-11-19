"""Disable Falcon's alternate-model-part entries (hand/face swaps) in Sonic's fighter file, in place.

Usage: python patch_modelparts.py <PlSn.dat in> <PlSn.dat out>
Each SBM_ModelPart's Count is set to 0 so the game no longer touches model parts by Falcon's numbering.
"""
import os, struct, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from hsd import *
src, dst = sys.argv[1], sys.argv[2]
raw = bytearray(open(src, "rb").read())
parts = list(HSDRawFile(src).Roots[0].Data.ModelPartAnimations.Array)
for i, p in enumerate(parts):
    b = bytes(p._s.GetData())
    print(f"part {i}: StartingBone {p.StartingBone} Count {p.Count} struct {b.hex()}")
    # locate: the non-pointer prefix (first 8 bytes) followed by two non-zero pointers
    hits, at = [], raw.find(b[:4])
    while at >= 0:
        p1, p2 = struct.unpack(">II", raw[at + 4:at + 12])
        if at % 4 == 0 and 0 < p1 < len(raw) and 0 < p2 < len(raw) and bytes(raw[0x20 + p1:0x20 + p1 + 2]) == bytes([p.Entries[0], p.Entries[1]]):
            hits.append(at)
        at = raw.find(b[:4], at + 4)
    if len(hits) != 1:
        raise SystemExit(f"part {i} located {len(hits)} times")
    before = bytes(raw[hits[0]:hits[0] + 4])
    p.Count = 0
    raw[hits[0]:hits[0] + 4] = bytes(p._s.GetData())[:4]
    print(f"   at 0x{hits[0]:X}: {before.hex()} -> {bytes(raw[hits[0]:hits[0]+4]).hex()}")
open(dst, "wb").write(raw)
chk = list(HSDRawFile(dst).Roots[0].Data.ModelPartAnimations.Array)
print("re-read counts:", [p.Count for p in chk])
