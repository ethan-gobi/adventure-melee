"""Point Sonic's model-part visibility tables at parts 0..N-1 by patching bytes in place (no HSDRaw re-save).

Usage: python patch_lookup.py <PlSn.dat in> <PlSn.dat out> <number of model parts>
The high-poly index array is overwritten with 0..N-1 (it is longer than N) and all four tables
(high poly, low poly, metal, metal main) are pointed at that one array with count N.
"""
import os, struct, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from hsd import *

src, dst, n = sys.argv[1], sys.argv[2], int(sys.argv[3])
raw = bytearray(open(src, "rb").read())
t = HSDRawFile(src).Roots[0].Data.ModelLookupTables.CostumeVisibilityLookups.Array[0]
old = {k: bytes(bytearray(getattr(t, k).Array[0].LookupEntries.Array[0].Entries)) for k in ("HighPoly", "LowPoly", "MetalPoly", "MetalMainModel")}

def find_once(b, what):
    i = raw.find(b)
    if i < 0 or raw.find(b, i + 1) >= 0:
        raise SystemExit(f"{what}: not found exactly once")
    return i

arr, structs = {}, {}
for k, v in old.items():
    # short arrays can occur inside longer ones, so accept the occurrence that a (count, pointer) entry refers to
    hits, i = [], raw.find(v)
    while i >= 0:
        e = struct.pack(">II", len(v), i - 0x20)
        j = raw.find(e)
        if j >= 0 and raw.find(e, j + 1) < 0:
            hits.append((i, j))
        i = raw.find(v, i + 1)
    if len(hits) != 1:
        raise SystemExit(f"{k}: located {len(hits)} times")
    arr[k], structs[k] = hits[0]
print("array file offsets:", {k: hex(v) for k, v in arr.items()}, "lengths", {k: len(v) for k, v in old.items()})
room = len(old["HighPoly"])
if arr["LowPoly"] == arr["HighPoly"] + len(old["HighPoly"]):
    room += len(old["LowPoly"])          # the low-poly array directly follows: both are free to reuse
if room < n:
    raise SystemExit(f"only {room} bytes available for {n} parts")
hi = arr["HighPoly"]
raw[hi:hi + n] = bytes(range(n))
for k, at in structs.items():
    raw[at:at + 8] = struct.pack(">II", n, hi - 0x20)
    print(f"{k}: {len(old[k])} entries -> {n} (parts 0..{n - 1})")
open(dst, "wb").write(raw)
chk = HSDRawFile(dst).Roots[0].Data.ModelLookupTables.CostumeVisibilityLookups.Array[0]
for k in old:
    e = getattr(chk, k).Array[0].LookupEntries.Array[0]
    assert e.Count == n and list(e.Entries)[:n] == list(range(n)), k
print("re-read ok; file size", len(raw), "(unchanged)" if len(raw) == os.path.getsize(src) else "")
