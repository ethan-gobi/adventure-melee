"""Clamp every model-part visibility list in Sonic's PlSn.dat to the parts his model really has, in place.

Usage: python patch_lookup_all.py <PlSn.dat in> <PlSn.dat out> <number of model parts in the costume> [--dry]
Melee hides every part listed in any set and then shows the selected set. Falcon's lists name parts that Sonic's model
does not have. In Sonic's file the lists were shortened to 18 entries but their counts still said 44 and 35, so the game read
past the list into other data and set flags through garbage pointers. Each over-long count is set to the part count.
"""
import struct, sys
src, dst, nparts = sys.argv[1], sys.argv[2], int(sys.argv[3])
raw = bytearray(open(src, "rb").read())
fsize, dsize, nrel, nroot, nref = struct.unpack(">5I", raw[:20])
D = 0x20
u32 = lambda o: struct.unpack(">I", raw[D + o:D + o + 4])[0]
rel = set(struct.unpack(f">{nrel}I", raw[D + dsize:D + dsize + 4 * nrel]))
root = struct.unpack(">II", raw[D + dsize + 4 * nrel:D + dsize + 4 * nrel + 8])[0]
L = u32(root + 8)
count, costumes = u32(L), u32(L + 4)
print(f"ftData at 0x{root:X}; lookup struct at 0x{L:X}: groups {count}, costume array 0x{costumes:X}; other fields {[hex(u32(L + k)) for k in (8, 12, 16, 20)]}")
# number of costumes: consecutive 16-byte entries of relocated pointers
nc = 0
while all((costumes + nc * 16 + k) in rel or u32(costumes + nc * 16 + k) == 0 for k in (0, 4, 8, 12)) and any((costumes + nc * 16 + k) in rel for k in (0, 4, 8, 12)):
    nc += 1
bad = cleared = 0
seen = set()
for c in range(nc):
    for ti, tname in enumerate(("HighPoly", "LowPoly", "MetalPoly", "MetalMain")):
        tp = costumes + c * 16 + ti * 4
        if tp not in rel:
            continue
        table = u32(tp)
        for g in range(count):
            gcount, gptr = u32(table + g * 8), u32(table + g * 8 + 4)
            if (table + g * 8 + 4) not in rel:
                continue
            for s in range(gcount):
                so = gptr + s * 8
                scount, sptr = u32(so), u32(so + 4)
                idx = list(raw[D + sptr:D + sptr + scount]) if (so + 4) in rel else []
                over = [i for i in idx if i >= nparts]
                if c == 0 or over:
                    print(f"  costume {c} {tname} group {g} set {s}: {scount} parts {idx[:12]}{'...' if scount > 12 else ''}" + (f"  OUT OF RANGE: {len(over)}" if over else ""))
                bad += len(over)
                if so not in seen and scount > nparts:
                    seen.add(so)
                    if idx[:nparts] != list(range(nparts)):
                        raise SystemExit("list does not start with 0..N-1; not clamping")
                    raw[D + so:D + so + 4] = struct.pack(">I", nparts)
                    print(f"    count {scount} -> {nparts}")
                    cleared += 1
print(f"costumes {nc}; out-of-range part indices found: {bad}; counts clamped: {cleared}")
if "--dry" not in sys.argv:
    open(dst, "wb").write(raw)
    print("written", dst, len(raw), "bytes (size unchanged)")
