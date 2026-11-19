"""Make a sharper spin-ball texture from Sonic's own model: the curled-up pose seen from the side, spin-blurred.

Usage: python make_spin_texture.py <out.png> [size]
Uses the same textures' colours as the model (no outside artwork). SA1's own sprite (stx_newspin) is only 64x64.
"""
import sys, os, io, math
import numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import sonic_moves as sm
from sonic_anim_lib import bd, COL, solve, Rx
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.collections import PolyCollection
from PIL import Image, ImageFilter

out = sys.argv[1]
size = int(sys.argv[2]) if len(sys.argv) > 2 else 128
R = 4.5
W, _ = solve(sm.tuck(0))
centre = (W[2] @ np.array([*sm.PIV, 1.0]))[:3]
tris = []
for g in bd["groups"]:
    col = next((c for k, c in COL.items() if k in g["image"]), "#999999")
    col = {"#2346c8": "#1838d8"}.get(col, col)
    c = g["c"]
    for n in range(0, len(c) - 2, 3):
        pts = [(W[c[n + j][0]] @ np.array([*c[n + j][1:4], 1.0]))[:3] - centre for j in range(3)]
        tris.append((col, pts))


BLUE = (0.05, 0.13, 0.78)


def render(angle, px=512):
    rot = Rx(angle)
    polys, cols, depth = [], [], []
    for col, pts in tris:
        q = [rot @ p for p in pts]
        polys.append([(p[2], p[1]) for p in q]); cols.append(col); depth.append(sum(p[0] for p in q))   # looking along -X: screen x = forward
    idx = np.argsort(depth)
    fig = plt.figure(figsize=(px / 100, px / 100), dpi=100, facecolor=BLUE)
    ax = fig.add_axes([0, 0, 1, 1]); ax.set_xlim(-R / 0.94, R / 0.94); ax.set_ylim(-R / 0.94, R / 0.94); ax.axis("off")
    ax.add_collection(PolyCollection([polys[i] for i in idx], facecolors=[cols[i] for i in idx], edgecolors="none", antialiased=True))
    buf = io.BytesIO(); fig.savefig(buf, format="png", facecolor=BLUE); plt.close(fig)
    return np.asarray(Image.open(buf).convert("RGB"), dtype=np.float32) / 255.0


N, SPAN = 36, 110.0
acc = np.zeros((512, 512, 3), dtype=np.float32); wsum = 0.0
for k in range(N):
    w = (1.0 - k / N) ** 1.6
    acc += render(-SPAN * k / N) * w
    wsum += w
acc /= wsum
img = 0.72 * acc + 0.28 * render(0)                       # spin blur plus a faint sharp image for detail
# make the streaks read: push saturation/contrast a little
mean = img.mean(axis=2, keepdims=True)
img = np.clip(mean + (img - mean) * 1.35, 0, 1)
yy, xx = np.mgrid[0:512, 0:512]
rr = np.hypot(xx - 255.5, yy - 255.5) / 255.5
img *= np.clip(1.08 - 0.42 * rr ** 2, 0, 1.08)[..., None]  # round shading toward the rim
ang = np.arctan2(-(yy - 255.5), xx - 255.5)
streak = np.exp(-((rr - 0.80) / 0.05) ** 2) * np.clip(np.cos(ang - math.radians(70)), 0, 1) ** 4
img += streak[..., None] * np.array([0.35, 0.45, 0.35])    # spin shine near the top rim
im = Image.fromarray((np.clip(img, 0, 1) * 255).astype(np.uint8)).resize((size, size), Image.LANCZOS).filter(ImageFilter.UnsharpMask(1.0, 50, 2))
im.save(out)
print("wrote", out, im.size)
