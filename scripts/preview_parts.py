"""Quick flat-shaded preview of a parts JSON (export_tails_pose / export_sonic_parts format), four views side by side.

Usage: python preview_parts.py <parts.json> <texture dir> <out.png>
"""
import json
import math
import os
import sys

import numpy as np
from PIL import Image, ImageDraw

d = json.load(open(sys.argv[1]))
tex = sys.argv[2]
cache = {}


def colour(mat):
    img = (d["materials"].get(mat) or {}).get("image")
    if not img:
        return (150, 150, 150)
    if img not in cache:
        p = os.path.join(tex, os.path.splitext(img)[0] + ".png")
        cache[img] = tuple(int(c) for c in np.asarray(Image.open(p).convert("RGB")).reshape(-1, 3).mean(0)) if os.path.exists(p) else (150, 150, 150)
    return cache[img]


tris = [(np.array([v["p"] for v in t["v"]]), colour(t["m"])) for p in d["parts"] for t in p["tris"]]
allp = np.concatenate([t[0] for t in tris])
c, ext = allp.mean(0), np.ptp(allp, 0).max()
S = 300
out = Image.new("RGB", (S * 4, S), (230, 230, 230))
for k, yaw in enumerate((0, 90, 180, 270)):
    r = math.radians(yaw)
    R = np.array([[math.cos(r), -math.sin(r), 0], [math.sin(r), math.cos(r), 0], [0, 0, 1]])   # about Z (Blender up)
    dr = ImageDraw.Draw(out)
    items = []
    for P, col in tris:
        q = (P - c) @ R.T
        items.append((q[:, 1].mean(), [(k * S + S / 2 + x * S * 0.8 / ext, S / 2 - z * S * 0.8 / ext) for x, y, z in q], col))
    for _, poly, col in sorted(items, key=lambda i: -i[0]):
        dr.polygon(poly, fill=col)
out.save(sys.argv[3])
print("preview", sys.argv[3])
