"""Offline close-up of Sonic's head (rest pose) from a model build's _bound.json, to judge the mouth and eyes.

Usage: python face_preview.py <PlSnNr_vNN_bound.json> <texture dir> <out.png> [mouth module]
Flat-shaded software render (orthographic, z-buffer): front, 3/4 and side views. Triangle colours are the SA1 texture
sampled at the triangle's centre. If a mouth module is given, its `mouth_parts(skin, W39)` returns extra
(name, triangles world-space Nx3x3, rgb) layers drawn on top of the head; each layer gets its own row.
"""
import importlib.util
import json
import math
import os
import sys

import numpy as np
from PIL import Image


def local_matrix(t):
    TX, TY, TZ, RX, RY, RZ, SX, SY, SZ = t[:9]
    cx, sx, cy, sy, cz, sz = math.cos(RX), math.sin(RX), math.cos(RY), math.sin(RY), math.cos(RZ), math.sin(RZ)
    rx = np.array([[1, 0, 0], [0, cx, -sx], [0, sx, cx]])
    ry = np.array([[cy, 0, sy], [0, 1, 0], [-sy, 0, cy]])
    rz = np.array([[cz, -sz, 0], [sz, cz, 0], [0, 0, 1]])
    m = np.eye(4)
    m[:3, :3] = rz @ ry @ rx @ np.diag([SX, SY, SZ])
    m[:3, 3] = [TX, TY, TZ]
    return m


def load(bound, tex_dir):
    d = json.load(open(bound))
    W = []
    for t in d["joints"]:
        W.append(local_matrix(t) if t[9] < 0 else W[t[9]] @ local_matrix(t))
    tris, cols, skin = [], [], []
    texc = {}
    for g in d["groups"]:
        img = texc.get(g["image"])
        if img is None:
            img = texc[g["image"]] = np.array(Image.open(os.path.join(tex_dir, g["image"] + ".png")).convert("RGB"), float)
        c = g["c"]
        for n in range(0, len(c) - 2, 3):
            p = [(W[c[n + k][0]] @ np.array([*c[n + k][1:4], 1.0]))[:3] for k in range(3)]
            u = np.mean([c[n + k][4] for k in range(3)]) % 1.0
            v = np.mean([c[n + k][5] for k in range(3)]) % 1.0
            h, w = img.shape[:2]
            col = img[min(h - 1, int(v * h)), min(w - 1, int(u * w))]
            if g["image"] in ("stx_btest1", "stx_head"):
                col = np.clip(col * 1.35, 0, 255)
            tris.append(p)
            cols.append(col)
            if g["image"] in ("stx_hada", "stx_hoho") and all(c[n + k][0] == 39 for k in range(3)):
                skin.append(p)                                   # world space, rest pose (as in the model build)
    return np.array(tris), np.array(cols), np.array(skin), W


def render(tris, cols, yaw, centre, scale, size=360):
    """orthographic view from direction yaw (0 = front, +90 = from Sonic's left), light from the camera."""
    r = math.radians(yaw)
    R = np.array([[math.cos(r), 0, -math.sin(r)], [0, 1, 0], [math.sin(r), 0, math.cos(r)]])
    P = (tris - centre) @ R.T
    img = np.full((size, size, 3), 200.0)
    zb = np.full((size, size), -1e9)
    L = np.array([0.3, 0.5, 1.0]); L /= np.linalg.norm(L)
    for t, col in zip(P, cols):
        n = np.cross(t[1] - t[0], t[2] - t[0])
        nn = np.linalg.norm(n)
        if nn < 1e-12:
            continue
        n /= nn
        shade = 0.45 + 0.55 * abs(n @ L)
        xy = np.stack([size / 2 + t[:, 0] * scale, size / 2 - t[:, 1] * scale], 1)
        x0, y0 = np.floor(xy.min(0)).astype(int)
        x1, y1 = np.ceil(xy.max(0)).astype(int)
        x0, y0, x1, y1 = max(x0, 0), max(y0, 0), min(x1, size - 1), min(y1, size - 1)
        if x0 > x1 or y0 > y1:
            continue
        gx, gy = np.meshgrid(np.arange(x0, x1 + 1) + 0.5, np.arange(y0, y1 + 1) + 0.5)
        a, b, c = xy
        den = (b[1] - c[1]) * (a[0] - c[0]) + (c[0] - b[0]) * (a[1] - c[1])
        if abs(den) < 1e-9:
            continue
        w0 = ((b[1] - c[1]) * (gx - c[0]) + (c[0] - b[0]) * (gy - c[1])) / den
        w1 = ((c[1] - a[1]) * (gx - c[0]) + (a[0] - c[0]) * (gy - c[1])) / den
        w2 = 1 - w0 - w1
        m = (w0 >= 0) & (w1 >= 0) & (w2 >= 0)
        z = w0 * t[0, 2] + w1 * t[1, 2] + w2 * t[2, 2]
        sub = zb[y0:y1 + 1, x0:x1 + 1]
        m &= z > sub
        sub[m] = z[m]
        img[y0:y1 + 1, x0:x1 + 1][m] = col * shade
    return img.astype(np.uint8)


def main():
    bound, tex_dir, out = sys.argv[1:4]
    tris, cols, skin, W = load(bound, tex_dir)
    head = W[39][:3, 3]
    keep = np.linalg.norm(tris.mean(1) - head, axis=1) < 9.0        # the head only
    tris, cols = tris[keep], cols[keep]
    layers = [("model", np.zeros((0, 3, 3)), (0, 0, 0))]
    if len(sys.argv) > 4:
        spec = importlib.util.spec_from_file_location("mouthmod", sys.argv[4])
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        layers = mod.mouth_parts(skin, W[39])
    centre = head + np.array([0.0, 2.0, 1.5])
    rows = []
    for name, extra, rgb in layers:
        parts = extra if rgb is None else [(extra, rgb)]          # rgb None: extra is a list of (triangles, rgb)
        T, C = tris, cols
        for e, c in parts:
            if len(e):
                T = np.concatenate([T, e])
                C = np.concatenate([C, np.tile(np.array(c, float), (len(e), 1))])
        extra = T[len(tris):]
        rows.append(np.concatenate([render(T, C, yaw, centre, 26) for yaw in (0, 40, 85)], 1))
        print(name, len(extra), "triangles")
    Image.fromarray(np.concatenate(rows, 0)).save(out)
    print("wrote", out)


if __name__ == "__main__":
    main()
