"""Pose Sonic's model with one of his animations at given frames and write textured OBJ files.

Usage: python pose_preview.py <bound.json> <PlSnAJ.dat> <anim name part> <frame>[,<frame>...] <out_prefix>
Writes <out_prefix>_<anim>_f<frame>.obj/.mtl (Melee units, Y up, Sonic faces +Z) for Blender rendering.
"""
import json
import math
import os
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from hsd import *  # noqa: E402,F401
from System.IO import File  # noqa: E402
from HSDRaw.Tools.Melee import FighterAJManager  # noqa: E402
from HSDRaw.Tools import FOBJ_Player  # noqa: E402

bound_json, aj_path, anim_part, frames_arg, out_prefix = sys.argv[1:6]
TEX = r"C:\adventure-melee\extract\sa1_tex\SONIC"
b = json.load(open(bound_json))
rest = [np.array(j[:9], dtype=float) for j in b["joints"]]
parent = [j[9] for j in b["joints"]]

aj = FighterAJManager(File.ReadAllBytes(aj_path))
syms = [s for s in aj.GetAnimationSymbols() if f"ACTION_{anim_part}" in s]
if not syms:
    raise SystemExit(f"no animation matching {anim_part}")
sym = sorted(syms, key=len)[0]
ft = HSDRawFile(aj.GetAnimationData(sym)).Roots[0].Data
CH = {"HSD_A_J_TRAX": 0, "HSD_A_J_TRAY": 1, "HSD_A_J_TRAZ": 2, "HSD_A_J_ROTX": 3, "HSD_A_J_ROTY": 4, "HSD_A_J_ROTZ": 5,
      "HSD_A_J_SCAX": 6, "HSD_A_J_SCAY": 7, "HSD_A_J_SCAZ": 8}
players = []
for bi in range(ft.Nodes.Count):
    tr = []
    for t in ft.Nodes[bi].Tracks:
        name = str(t.JointTrackType)
        if name in CH:
            tr.append((CH[name], FOBJ_Player(t.ToFOBJ())))
    players.append(tr)


def mat(v):
    tx, ty, tz, rx, ry, rz, sx, sy, sz = v
    cx, sxn, cy, syn, cz, szn = math.cos(rx), math.sin(rx), math.cos(ry), math.sin(ry), math.cos(rz), math.sin(rz)
    R = np.array([[1, 0, 0], [0, cx, -sxn], [0, sxn, cx]])
    R = np.array([[cy, 0, syn], [0, 1, 0], [-syn, 0, cy]]) @ R
    R = np.array([[cz, -szn, 0], [szn, cz, 0], [0, 0, 1]]) @ R
    m = np.eye(4)
    m[:3, :3] = R @ np.diag([sx, sy, sz])
    m[:3, 3] = [tx, ty, tz]
    return m


def world(frame):
    W = []
    for i, v in enumerate(rest):
        v = v.copy()
        if i < len(players):
            for ch, pl in players[i]:
                v[ch] = pl.GetValue(float(frame))
        W.append(mat(v) if parent[i] < 0 else W[parent[i]] @ mat(v))
    return W


rest_W = []
for i, v in enumerate(rest):
    rest_W.append(mat(v) if parent[i] < 0 else rest_W[parent[i]] @ mat(v))

short = sym.split("ACTION_")[1].replace("_figatree", "")
print("animation", sym, "frames", ft.FrameCount)
for fr in [float(x) for x in frames_arg.split(",")]:
    W = world(fr)
    base = f"{out_prefix}_{short}_f{int(fr)}"
    mtl = [f"newmtl m{k}\nKd 1 1 1\nmap_Kd {os.path.join(TEX, g['image'] + '.png')}\n" for k, g in enumerate(b["groups"])]
    lines = [f"mtllib {os.path.basename(base)}.mtl"]
    vi = 0
    for k, g in enumerate(b["groups"]):
        lines.append(f"usemtl m{k}")
        for n, (bone, x, y, z, u, v) in enumerate(g["c"]):
            p = W[bone] @ np.array([x, y, z, 1.0])
            lines.append(f"v {p[0]:.4f} {p[1]:.4f} {p[2]:.4f}")
            lines.append(f"vt {u:.4f} {1 - v:.4f}")
            vi += 1
            if n % 3 == 2:
                lines.append(f"f {vi - 2}/{vi - 2} {vi - 1}/{vi - 1} {vi}/{vi}")
    open(base + ".obj", "w").write("\n".join(lines) + "\n")
    open(base + ".mtl", "w").write("\n".join(mtl))
    head = W[39][:3, 3]
    print(f"frame {fr:5.1f}: wrote {base}.obj | head bone at {np.round(head, 2)}, head pitch vs rest "
          f"{math.degrees(math.atan2(-(W[39][:3, :3] @ np.linalg.inv(rest_W[39][:3, :3]))[1, 2], (W[39][:3, :3] @ np.linalg.inv(rest_W[39][:3, :3]))[2, 2])):.0f} deg")
