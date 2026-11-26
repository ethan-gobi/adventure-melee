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
p = shot(8.0, head + np.array([0.0, 2.0, 1.5]), 42, 30, 400).resize((136, 136), Image.LANCZOS)   # v68: head only (v67 showed the T-pose arms)
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
# series emblem (v74): white silhouette of his head in profile (quills out the back), alpha from the render
keep = np.linalg.norm(tris.mean(1) - head, axis=1) < 10.0              # whole head incl. quills (no arm filter here)
e = render(tris[keep], cols[keep], 90, head + np.array([0.0, 1.0, -1.5]), 20, size=300)
ea = np.asarray(e).astype(int)
solid = ~np.all(np.abs(ea[..., :3] - 200) <= 1, axis=-1)
outside = np.zeros_like(solid)                                     # flood the background from the border; holes get filled
stack = [(0, 0), (0, 299), (299, 0), (299, 299)]
while stack:
    yy, xx = stack.pop()
    if 0 <= yy < 300 and 0 <= xx < 300 and not outside[yy, xx] and not solid[yy, xx]:
        outside[yy, xx] = True
        stack += [(yy + 1, xx), (yy - 1, xx), (yy, xx + 1), (yy, xx - 1)]
sil = np.zeros((300, 300, 4), dtype=np.uint8)
sil[..., :3] = 255
sil[..., 3] = np.where(outside, 0, 255)
em = Image.fromarray(sil, "RGBA").transpose(Image.FLIP_LEFT_RIGHT)      # facing right, quills to the left
em = em.crop(em.getbbox())
side = int(max(em.size) * 1.12)
sq = Image.new("RGBA", (side, side), (255, 255, 255, 0))
sq.paste(em, ((side - em.width) // 2, (side - em.height) // 2), em)
sq.resize((128, 128), Image.LANCZOS).save(os.path.join(out, "emblem.png"))
print("written", os.path.join(out, "emblem.png"))
