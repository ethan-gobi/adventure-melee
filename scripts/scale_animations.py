"""v05: scale Sonic's animation translation keys to his shortened bones, rebuild the AJ file,
repoint the fighter's action table, and resize hurtboxes.

Usage: python scale_animations.py <PlSnAJ.dat in> <PlSn.dat in> <bone_factors.json> <PlSnAJ.dat out> <PlSn.dat out>
Only Sonic's copies (PlSnAJ.dat / PlSn.dat) are written; Falcon's files are never touched.
"""
import json
import os
import sys
import tempfile

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from hsd import *  # noqa: E402,F401
from System.IO import File  # noqa: E402
from HSDRaw.Tools.Melee import FighterAJManager  # noqa: E402
from HSDRaw.Tools import FOBJFrameEncoder  # noqa: E402
import sonic_proportions as sp  # noqa: E402

aj_in, pl_in, fac_json, aj_out, pl_out = sys.argv[1:6]
factors = {int(k): v for k, v in json.load(open(fac_json)).items()}
TRA = ("HSD_A_J_TRAX", "HSD_A_J_TRAY", "HSD_A_J_TRAZ")
# shield bubble centre (bone 61) in the shield animations: higher than the plain body scale so the bubble covers Sonic's big head
GUARD_SHIELD = {61: 0.85}

aj = FighterAJManager(File.ReadAllBytes(aj_in))
syms = list(aj.GetAnimationSymbols())
order = sorted(syms, key=lambda s: aj.GetOffsetSize(s).Item1)
tmp = tempfile.mkdtemp(prefix="aj_")
tracks_scaled = 0
max_err = 0.0
for i, sym in enumerate(order):
    f = HSDRawFile(aj.GetAnimationData(sym))
    ft = f.Roots[0].Data
    nodes = ft.Nodes
    changed = False
    for bi in range(nodes.Count):
        fct = factors.get(bi)
        if "ACTION_Guard" in sym and bi in GUARD_SHIELD:
            fct = GUARD_SHIELD[bi]
        if fct is None or abs(fct - 1.0) < 1e-6:
            continue
        node = nodes[bi]
        for ti in range(node.Tracks.Count):
            tr = node.Tracks[ti]
            if str(tr.JointTrackType) not in TRA:
                continue
            keys = tr.ToFOBJ().GetDecodedKeys()
            want = []
            for k in keys:
                k.Value = k.Value * fct
                k.Tan = k.Tan * fct
                want.append(k.Value)
            fobj = FOBJFrameEncoder.EncodeFrames(keys, tr.JointTrackType, 0.0001)
            tr.FromFOBJ(fobj)
            got = [k.Value for k in tr.ToFOBJ().GetDecodedKeys()]
            if len(got) == len(want):
                max_err = max(max_err, max((abs(a - b) for a, b in zip(got, want)), default=0.0))
            else:
                raise SystemExit(f"{sym} bone {bi}: key count changed {len(want)} -> {len(got)}")
            tracks_scaled += 1
            changed = True
    if changed:
        ft.Nodes = nodes
        p = os.path.join(tmp, f"{i}.dat")
        f.Save(p)
        aj.SetAnimation(sym, File.ReadAllBytes(p))
print(f"animations: {len(order)}, translation tracks scaled: {tracks_scaled}, max re-encode error: {max_err:.5f}")

new_aj = bytes(aj.RebuildAJFile(order, False))
open(aj_out, "wb").write(new_aj)
# offsets are only known by the manager that did the rebuild ("Must Call Rebuild First")
pos = {s: (aj.GetOffsetSize(s).Item1, aj.GetOffsetSize(s).Item2) for s in order}
bad = [s for s, (o, z) in pos.items() if o < 0 or o + z > len(new_aj)]
if bad:
    raise SystemExit(f"invalid offsets for {len(bad)} animations, e.g. {bad[:3]}")
for s_, (o, z) in pos.items():   # every offset must point at that animation's own bytes
    if new_aj[o:o + z] != bytes(aj.GetAnimationData(s_)):
        raise SystemExit(f"offset check failed for {s_}")
print(f"offset check: all {len(pos)} animations found at their new offsets")
print(f"AJ file: {os.path.getsize(aj_in)} -> {len(new_aj)} bytes")

# ---- fighter data: patch bytes in place (a full HSDRaw re-save of these tables crashes the game)
import struct  # noqa: E402

pl = HSDRawFile(pl_in)
fd = pl.Roots[0].Data
raw = bytearray(open(pl_in, "rb").read())
actions = list(fd.FighterActionTable.Commands)
old = [(a.AnimationOffset, a.AnimationSize) for a in actions]
names = [a.SymbolName.Value if a.SymbolName is not None else None for a in actions]
STRIDE = 0x18
hits = []
probe = [struct.pack(">ii", *o) for o in old]
start = 0
while True:
    i = raw.find(probe[0], start)
    if i < 0:
        break
    base = i - 4
    if all(raw[base + k * STRIDE + 4: base + k * STRIDE + 12] == probe[k] for k in range(len(old))):
        hits.append(base)
    start = i + 4
if len(hits) != 1:
    raise SystemExit(f"action table located {len(hits)} times; refusing to patch")
base = hits[0]
moved = 0
for k, name in enumerate(names):
    if name in pos:
        if old[k] != pos[name]:
            moved += 1
        raw[base + k * STRIDE + 4: base + k * STRIDE + 12] = struct.pack(">ii", *pos[name])
print(f"action table at file offset 0x{base:X}: {len(actions)} actions, {moved} animation offsets/sizes updated")

for i, h in enumerate(fd.Hurtboxes.Hurtboxes):
    bone, p1, p2, r = sp.HURTBOXES[i]
    if h.BoneIndex != bone:
        raise SystemExit(f"hurtbox {i} is on bone {h.BoneIndex}, expected {bone}")
    before = bytes(h._s.GetData())
    oldtxt = f"({h.X1:.2f},{h.Y1:.2f},{h.Z1:.2f})-({h.X2:.2f},{h.Y2:.2f},{h.Z2:.2f}) r{h.Size:.2f}"
    h.X1, h.Y1, h.Z1 = p1
    h.X2, h.Y2, h.Z2 = p2
    h.Size = r
    after = bytes(h._s.GetData())
    at = raw.find(before)
    if at < 0 or raw.find(before, at + 1) >= 0:
        raise SystemExit(f"hurtbox {i} bytes not found exactly once")
    raw[at:at + len(after)] = after
    print(f"hurtbox {i:2} bone {bone:2}: {oldtxt} -> ({p1[0]:.2f},{p1[1]:.2f},{p1[2]:.2f})-({p2[0]:.2f},{p2[1]:.2f},{p2[2]:.2f}) r{r:.2f}")
open(pl_out, "wb").write(raw)

chk = HSDRawFile(pl_out).Roots[0].Data
ca = list(chk.FighterActionTable.Commands)
wrong = [a.SymbolName.Value for a in ca if a.SymbolName is not None and a.SymbolName.Value in pos and (a.AnimationOffset, a.AnimationSize) != pos[a.SymbolName.Value]]
hb = list(chk.Hurtboxes.Hurtboxes)
hb_ok = all(abs(h.Size - sp.HURTBOXES[i][3]) < 1e-4 and abs(h.X2 - sp.HURTBOXES[i][2][0]) < 1e-4 for i, h in enumerate(hb))
print(f"re-read check: {len(ca)} actions, {len(wrong)} with wrong offsets; {len(hb)} hurtboxes, values {'match' if hb_ok else 'DO NOT MATCH'}; file size {os.path.getsize(pl_in)} -> {len(raw)}")
if wrong or not hb_ok:
    raise SystemExit("patch did not persist")
print("saved", aj_out, "and", pl_out)
