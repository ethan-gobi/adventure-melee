"""v08 moveset pass 1 (data only, Falcon's animations and timings kept).

1. Refit every hitbox in Sonic's scripts to his smaller v07 body: offsets scaled per bone, sizes x0.75.
2. Set the approved damage values on jabs, tilts, smashes, aerials and pummel.

Usage: python patch_moveset_v08.py <PlSn.dat in> <PlSn.dat out> <changes.md out>
Hitbox commands are edited in place (same bytes, same length); nothing else in the file moves.
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import subactions as sa  # noqa: E402

src, dst, report = sys.argv[1:4]

# offset scale per bone = how much that bone's segment shrank in v07 (scripts/sonic_proportions.py)
BONE_SCALE = {7: 0.42, 13: 0.42, 8: 0.62, 14: 0.62, 23: 0.43, 45: 0.43, 24: 0.76, 46: 0.76}
DEFAULT_SCALE = 0.69          # hip-height ratio; used for bone 0 (ground-relative) and the torso bones
SIZE_SCALE = 0.75

# action name prefix -> {(old damage, old angle or None): {field: new value}}
D = "Damage"
MOVES = {
    "Attack11": {(2, None): {D: 3}},
    "Attack13": {(8, None): {D: 5}, (6, None): {D: 5}},
    "AttackDash": {(10, None): {D: 9}, (7, None): {D: 6}},
    "AttackS3": {(12, None): {D: 9}, (11, None): {D: 9}, (10, None): {D: 9}},
    "AttackHi3": {(13, None): {D: 8}},
    "AttackLw3": {(12, None): {D: 7}},
    "AttackS4": {(21, None): {D: 15, "Element": 0}, (20, None): {D: 15, "Element": 0}, (19, None): {D: 15, "Element": 0}},
    "AttackHi4": {(8, None): {D: 5}, (13, None): {D: 8}, (14, None): {D: 8}, (12, None): {D: 8}},
    "AttackLw4": {(18, None): {D: 13}, (16, None): {D: 13}},
    "AttackAirN": {(6, None): {D: 4}, (5, None): {D: 4}, (7, None): {D: 5}},
    "AttackAirF": {(18, None): {D: 12, "Angle": 270, "Element": 0}, (6, None): {D: 7}},
    "AttackAirB": {(14, None): {D: 12}},
    "AttackAirHi": {(13, 361): {D: 10}, (12, 361): {D: 10}, (12, 30): {D: 8}, (10, 30): {D: 8}, (8, 0): {D: 6}, (6, 0): {D: 6}},
    "AttackAirLw": {(16, 270): {D: 13, "Angle": 361}, (16, 290): {D: 13, "Angle": 361}},
    "CatchAttack": {(3, None): {D: 2}},
}

raw = bytearray(open(src, "rb").read())
acts = sa.load(src)
lines = ["| Action | Hitbox | Field | From | To |", "|---|---|---|---|---|"]
refit = 0
# locate the action table (0x18-byte entries: name ptr, anim offset, anim size, script ptr, flags, 0)
import struct
from hsd import HSDRawFile
tbl = list(HSDRawFile(src).Roots[0].Data.FighterActionTable.Commands)
probe = [struct.pack(">ii", a.AnimationOffset, a.AnimationSize) for a in tbl]
hits, start = [], 0
while True:
    i = raw.find(probe[0], start)
    if i < 0:
        break
    if all(raw[i - 4 + k * 0x18 + 4: i - 4 + k * 0x18 + 12] == probe[k] for k in range(len(probe))):
        hits.append(i - 4)
    start = i + 4
if len(hits) != 1:
    raise SystemExit(f"action table located {len(hits)} times")
base = hits[0]
done_offsets = set()
skipped = []
for act in acts:
    if not any(c["name"] == "Create Hitbox" for c in act.cmds):
        continue
    loc = 0x20 + struct.unpack(">I", raw[base + act.index * 0x18 + 0x0C: base + act.index * 0x18 + 0x10])[0]
    if loc in done_offsets:
        continue          # several actions can point at one script
    done_offsets.add(loc)
    data = bytearray(raw[loc:loc + len(act.data)])
    cmds = sa.parse(bytes(data))
    if [c["name"] for c in cmds] != [c["name"] for c in act.cmds]:
        skipped.append(act.name)
        continue
    rules = next((r for k, r in MOVES.items() if act.name and act.name.startswith(k)), {})
    for c in cmds:
        if c["name"] != "Create Hitbox":
            continue
        p = dict(c["params"])
        sc = BONE_SCALE.get(p["Bone"], DEFAULT_SCALE)
        for fld in ("X-Offset", "Y-Offset", "Z-Offset"):
            sa.set_param(data, c, fld, int(round(p[fld] * sc)))
        sa.set_param(data, c, "Size", int(round(p["Size"] * SIZE_SCALE)))
        refit += 1
        rule = rules.get((p["Damage"], p["Angle"])) or rules.get((p["Damage"], None))
        if rule:
            for fld, val in rule.items():
                if p[fld] != val:
                    lines.append(f"| {act.name} | {p['ID']} | {fld} | {p[fld]} | {val} |")
                    sa.set_param(data, c, fld, val)
    raw[loc:loc + len(data)] = data
if skipped:
    raise SystemExit(f"script bytes did not match for: {skipped}")
open(dst, "wb").write(raw)

# verify by decoding the written file
after = {a.index: a for a in sa.load(dst)}
bad = 0
for act in acts:
    b = after[act.index]
    if len(b.data) != len(act.data) or [c["name"] for c in b.cmds] != [c["name"] for c in act.cmds]:
        bad += 1
with open(report, "w") as f:
    f.write(f"Hitboxes refit: {refit} (offsets x bone scale {BONE_SCALE}, others x{DEFAULT_SCALE}; sizes x{SIZE_SCALE})\n\n")
    f.write("\n".join(lines) + "\n")
print(f"hitboxes refit: {refit}; value changes: {len(lines) - 2}; scripts whose structure changed: {bad}; file size {os.path.getsize(src)} -> {len(raw)}")
