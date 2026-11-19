"""Retarget SA1 Sonic animations onto Sonic's Melee skeleton and put them in his animation file.

Usage: python retarget_sa1.py <bound.json> <PlSnAJ in> <PlSn.dat in> <PlSnAJ out> <PlSn.dat out> <ACTION=sa1json> [...]
  e.g. Wait1=work/sa1anim/s_wait0.json
Each mapped Melee bone gets the SA1 node's world-space rotation change, corrected for how that part was
placed on the bone when the model was built. Unmapped bones stay at rest. Hip height follows the SA1 root.
Only Sonic's files are written; PlSn.dat is byte-patched (animation offsets/sizes only).
"""
import json
import math
import os
import struct
import sys
import tempfile

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from hsd import *  # noqa: E402,F401
from System.IO import File  # noqa: E402
from System.Collections.Generic import List  # noqa: E402
from HSDRaw.Tools.Melee import FighterAJManager  # noqa: E402
from HSDRaw.Tools import FOBJKey, FOBJFrameEncoder  # noqa: E402
from HSDRaw.Common.Animation import HSD_Track, JointTrackType  # noqa: E402
from HSDRaw.Common.Animation import GXInterpolationType  # noqa: E402

bound_json, aj_in, pl_in, aj_out, pl_out = sys.argv[1:6]
jobs = [a.split("=", 1) for a in sys.argv[6:]]

bd = json.load(open(bound_json))
rest = [np.array(j[:9], dtype=float) for j in bd["joints"]]
parent = [j[9] for j in bd["joints"]]
K = bd["K"]
C = np.array([[0, -1, 0], [0, 0, 1], [-1, 0, 0]], dtype=float)   # Blender -> Melee axes (sonic_proportions.S)


def mat(v):
    tx, ty, tz, rx, ry, rz, sx, sy, sz = v
    cx, sxn, cy, syn, cz, szn = math.cos(rx), math.sin(rx), math.cos(ry), math.sin(ry), math.cos(rz), math.sin(rz)
    R = np.array([[cz, -szn, 0], [szn, cz, 0], [0, 0, 1]]) @ np.array([[cy, 0, syn], [0, 1, 0], [-syn, 0, cy]]) @ np.array([[1, 0, 0], [0, cx, -sxn], [0, sxn, cx]])
    m = np.eye(4)
    m[:3, :3] = R @ np.diag([sx, sy, sz])
    m[:3, 3] = [tx, ty, tz]
    return m


rest_W = []
for i, v in enumerate(rest):
    rest_W.append(mat(v) if parent[i] < 0 else rest_W[parent[i]] @ mat(v))


def rot_of(lin):
    u, _, vt = np.linalg.svd(np.array(lin))
    r = u @ vt
    return r if np.linalg.det(r) > 0 else -r


# Melee bone <- (SA1 node that carries the motion, SA1 part whose placement defines the binding)
MAP = {2: ("001", None), 19: ("010", "010"), 39: ("022", "022"),
       45: ("025", "034"), 46: ("027", "029"), 47: ("030", "030"),
       23: ("036", "045"), 24: ("038", "040"), 25: ("041", "041"),
       13: ("047", "055"), 14: ("049", "051"), 16: ("052", "052"),
       7: ("057", "065"), 8: ("059", "061"), 10: ("062", "062")}
PLACE = {b: (rot_of(bd["maps"][p]["lin"]) if p else np.eye(3)) for b, (_, p) in MAP.items()}


def euler_zyx(R):
    """R = Rz @ Ry @ Rx -> (rx, ry, rz)."""
    ry = math.asin(max(-1.0, min(1.0, -R[2, 0])))
    rx = math.atan2(R[2, 1], R[2, 2])
    rz = math.atan2(R[1, 0], R[0, 0])
    return rx, ry, rz


def retarget(sa):
    r0 = {k: np.array(v) for k, v in sa["rest"].items()}
    out = []   # per frame: {bone: (tx,ty,tz, rx,ry,rz)}
    for fr in sa["frames"]:
        m = {k: np.array(v) for k, v in fr.items()}
        W = [None] * len(rest)
        vals = {}
        for i, v in enumerate(rest):
            pw = np.eye(4) if parent[i] < 0 else W[parent[i]]
            if i in MAP:
                node = MAP[i][0]
                D = C @ m[node][:3, :3] @ np.linalg.inv(r0[node][:3, :3]) @ C.T
                target = D @ PLACE[i].T @ rest_W[i][:3, :3]
                local = np.linalg.inv(pw[:3, :3]) @ target
                rx, ry, rz = euler_zyx(local)
                t = v[:3].copy()
                if i == 2:   # hip height and sway follow the SA1 root, in Melee units
                    dp = C @ (m[node][:3, 3] - r0[node][:3, 3]) * K
                    t = t + np.linalg.inv(pw[:3, :3]) @ np.array([0.0, dp[1], 0.0])
                vv = np.array([*t, rx, ry, rz, *v[6:9]])
                vals[i] = (*t, rx, ry, rz)
            else:
                vv = v
            W[i] = pw @ mat(vv)
        out.append(vals)
    return out


def unwrap(seq):
    o = [seq[0]]
    for a in seq[1:]:
        while a - o[-1] > math.pi:
            a -= 2 * math.pi
        while a - o[-1] < -math.pi:
            a += 2 * math.pi
        o.append(a)
    return o


TT = [JointTrackType.HSD_A_J_TRAX, JointTrackType.HSD_A_J_TRAY, JointTrackType.HSD_A_J_TRAZ,
      JointTrackType.HSD_A_J_ROTX, JointTrackType.HSD_A_J_ROTY, JointTrackType.HSD_A_J_ROTZ]

aj = FighterAJManager(File.ReadAllBytes(aj_in))
syms = list(aj.GetAnimationSymbols())
order = sorted(syms, key=lambda s: aj.GetOffsetSize(s).Item1)
tmp = tempfile.mkdtemp(prefix="rt_")
for action, sa_path in jobs:
    sa = json.load(open(sa_path))
    frames = retarget(sa)
    sym = [s for s in syms if s.endswith(f"ACTION_{action}_figatree")]
    if len(sym) != 1:
        raise SystemExit(f"animation for {action} not found exactly once")
    sym = sym[0]
    f = HSDRawFile(aj.GetAnimationData(sym))
    ft = f.Roots[0].Data
    nodes = ft.Nodes
    n = len(frames)
    for bi in range(nodes.Count):
        node = nodes[bi]
        node.Tracks.Clear()
        if bi not in MAP:
            continue
        chans = list(zip(*[fr[bi] for fr in frames]))
        for ci, tt in enumerate(TT):
            if ci < 3 and bi != 2:
                continue
            series = unwrap(list(chans[ci])) if ci >= 3 else list(chans[ci])
            if max(series) - min(series) < 1e-5 and abs(series[0] - rest[bi][ci]) < 1e-5:
                continue
            keys = List[FOBJKey]()
            for k, val in enumerate(series):
                key = FOBJKey()
                key.Frame = float(k)
                key.Value = float(val)
                key.InterpolationType = GXInterpolationType.HSD_A_OP_LIN
                keys.Add(key)
            node.Tracks.Add(HSD_Track(FOBJFrameEncoder.EncodeFrames(keys, tt, 0.0005)))
    ft.Nodes = nodes
    ft.FrameCount = float(n - 1)
    p = os.path.join(tmp, f"{action}.dat")
    f.Save(p)
    aj.SetAnimation(sym, File.ReadAllBytes(p))
    print(f"{action}: replaced with {os.path.basename(sa_path)} ({n} frames)")

new_aj = bytes(aj.RebuildAJFile(order, False))
open(aj_out, "wb").write(new_aj)
pos = {s: (aj.GetOffsetSize(s).Item1, aj.GetOffsetSize(s).Item2) for s in order}
for s_, (o, z) in pos.items():
    if o < 0 or new_aj[o:o + z] != bytes(aj.GetAnimationData(s_)):
        raise SystemExit(f"offset check failed for {s_}")

raw = bytearray(open(pl_in, "rb").read())
acts = list(HSDRawFile(pl_in).Roots[0].Data.FighterActionTable.Commands)
old = [struct.pack(">ii", a.AnimationOffset, a.AnimationSize) for a in acts]
hits, start = [], 0
while True:
    i = raw.find(old[0], start)
    if i < 0:
        break
    if all(raw[i - 4 + k * 0x18 + 4: i - 4 + k * 0x18 + 12] == old[k] for k in range(len(old))):
        hits.append(i - 4)
    start = i + 4
if len(hits) != 1:
    raise SystemExit(f"action table located {len(hits)} times")
moved = 0
for k, a in enumerate(acts):
    name = a.SymbolName.Value if a.SymbolName is not None else None
    if name in pos:
        new = struct.pack(">ii", *pos[name])
        if raw[hits[0] + k * 0x18 + 4: hits[0] + k * 0x18 + 12] != new:
            moved += 1
        raw[hits[0] + k * 0x18 + 4: hits[0] + k * 0x18 + 12] = new
open(pl_out, "wb").write(raw)
chk = list(HSDRawFile(pl_out).Roots[0].Data.FighterActionTable.Commands)
bad = sum(1 for a in chk if a.SymbolName is not None and a.SymbolName.Value in pos and (a.AnimationOffset, a.AnimationSize) != pos[a.SymbolName.Value])
print(f"AJ {os.path.getsize(aj_in)} -> {len(new_aj)} bytes; offsets updated {moved}; re-read errors {bad}")
if bad:
    raise SystemExit("offset patch failed")
