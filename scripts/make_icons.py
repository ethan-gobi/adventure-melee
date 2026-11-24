"""Sonic's character-select portrait (csp.png, 136x188) and stock icon (stc.png, 24x24), rendered from his own model.

Usage: python make_icons.py <model _bound.json> <texture dir> <out dir>
Background is transparent (the renderer's flat 200-grey background is keyed out).
"""
import os
import sys

import numpy as np
from PIL import Image

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from face_preview import load, render  # noqa: E402

bound, tex_dir, out = sys.argv[1:4]
tris, cols, skin, W = load(bound, tex_dir)
head = W[39][:3, 3]


def shot(keep_r, centre, scale, yaw, size):
    keep = (np.linalg.norm(tris.mean(1) - head, axis=1) < keep_r) & (np.abs(tris.mean(1)[:, 0] - head[0]) < 2.9)   # no T-pose arms
    img = render(tris[keep], cols[keep], yaw, centre, scale, size=size)
    a = np.asarray(img).astype(np.uint8) if not isinstance(img, Image.Image) else np.asarray(img)
    rgb = a[..., :3]
    bg = np.all(np.abs(rgb.astype(int) - 200) <= 1, axis=-1)
    alpha = np.where(bg, 0, 255).astype(np.uint8)
    return Image.fromarray(np.dstack([rgb, alpha]), "RGBA")


os.makedirs(out, exist_ok=True)
# portrait: head and shoulders, three-quarter view
p = shot(11.0, head + np.array([0.0, 0.5, 1.0]), 30, 30, 400).resize((136, 136), Image.LANCZOS)
csp = Image.new("RGBA", (136, 188), (0, 0, 0, 0))
csp.paste(p, (0, 20), p)
csp.save(os.path.join(out, "csp.png"))
# stock icon: the head, nearly front-on
s = shot(7.5, head + np.array([0.0, 2.0, 1.5]), 26, 20, 300).resize((24, 24), Image.LANCZOS)
s.save(os.path.join(out, "stc.png"))
print("written", os.path.join(out, "csp.png"), os.path.join(out, "stc.png"))
# select-screen grid icon source (build_iso.ps1 -IconPng scales it to the slot's own size)
g = shot(7.5, head + np.array([0.0, 2.0, 1.5]), 26, 25, 300).resize((128, 128), Image.LANCZOS)
g.save(os.path.join(out, "css_icon.png"))
print("written", os.path.join(out, "css_icon.png"))
