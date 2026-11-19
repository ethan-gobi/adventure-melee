"""Append the root symbol(s) of one HSD .dat file to another WITHOUT re-serialising the target.

Usage: python append_dat_root.py <target.dat> <donor.dat> <out.dat>
The target's existing data bytes, pointer offsets, roots and strings are kept exactly; the donor's data is
appended (0x20 aligned), its relocations shifted, and its roots added with their names.
DAT layout: 0x20 header [file size, data size, reloc count, root count, ref count, ...], data, reloc table
(u32 offsets of pointers, relative to data start), root table (u32 data offset, u32 string offset),
reference table (same shape), string table.
"""
import struct
import sys


def read(path):
    b = open(path, "rb").read()
    fsize, dsize, nrel, nroot, nref = struct.unpack(">5I", b[:20])
    data = b[0x20:0x20 + dsize]
    p = 0x20 + dsize
    rel = list(struct.unpack(f">{nrel}I", b[p:p + 4 * nrel])); p += 4 * nrel
    roots = [struct.unpack(">II", b[p + 8 * i:p + 8 * i + 8]) for i in range(nroot)]; p += 8 * nroot
    refs = [struct.unpack(">II", b[p + 8 * i:p + 8 * i + 8]) for i in range(nref)]; p += 8 * nref
    strings = b[p:fsize]
    hdr_rest = b[20:0x20]
    return dict(data=bytearray(data), rel=rel, roots=roots, refs=refs, strings=strings, hdr=hdr_rest)


def name_at(strings, off):
    return strings[off:strings.index(b"\0", off)].decode()


tgt, donor, out = sys.argv[1:4]
a, d = read(tgt), read(donor)
if d["refs"]:
    raise SystemExit("donor has reference entries; not supported")
existing = {name_at(a["strings"], s) for _, s in a["roots"]}
base = (len(a["data"]) + 0x1F) & ~0x1F
data = a["data"] + bytes(base - len(a["data"]))
dd = d["data"]
# shift internal pointers of the donor data by 'base'
for r in d["rel"]:
    v = struct.unpack(">I", dd[r:r + 4])[0]
    dd[r:r + 4] = struct.pack(">I", v + base)
data += dd
rel = a["rel"] + [r + base for r in d["rel"]]
strings = bytearray(a["strings"])
roots = list(a["roots"])
for off, s in d["roots"]:
    name = name_at(d["strings"], s)
    if name in existing:
        raise SystemExit(f"target already has a root named {name}")
    roots.append((off + base, len(strings)))
    strings += name.encode() + b"\0"
    print(f"added root {name} at data offset 0x{off + base:X} ({len(dd)} bytes of code/data, {len(d['rel'])} pointers)")
body = bytes(data) + struct.pack(f">{len(rel)}I", *rel) + b"".join(struct.pack(">II", *r) for r in roots) \
    + b"".join(struct.pack(">II", *r) for r in a["refs"]) + bytes(strings)
fsize = 0x20 + len(body)
hdr = struct.pack(">5I", fsize, len(data), len(rel), len(roots), len(a["refs"])) + a["hdr"]
open(out, "wb").write(hdr + body)
# verify: the target's original data region is byte-identical
chk = read(out)
assert chk["data"][:len(a["data"])] == a["data"], "original data changed"
assert chk["rel"][:len(a["rel"])] == a["rel"] and chk["roots"][:len(a["roots"])] == a["roots"]
print(f"{tgt}: {len(open(tgt, 'rb').read())} -> {fsize} bytes; original data/relocs/roots unchanged")
