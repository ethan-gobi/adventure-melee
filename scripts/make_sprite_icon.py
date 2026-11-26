"""Stock icon from the user's classic sprite sheet: the head of the second sprite (Sonic 2), body removed, white
background keyed out (only the white connected to the border, so the eyes stay white), scaled to 24x24.

Usage: python make_sprite_icon.py <sprite sheet png> <out dir> [sprite number, default 2]
"""
import os
import sys

import numpy as np
from PIL import Image

sheet, out = sys.argv[1], sys.argv[2]
n = int(sys.argv[3]) if len(sys.argv) > 3 else 2
im = np.asarray(Image.open(sheet).convert("RGBA")).astype(int)
H = int(im.shape[0] * 0.66)                                        # sprites are above the logos
ink = (im[:H, :, :3].min(axis=2) < 235) & (im[:H, :, 3] > 0)
cols = np.where(ink.any(axis=0))[0]
runs, start = [], cols[0]
for a, b in zip(cols, cols[1:]):
    if b - a > 20:
        runs.append((start, a)); start = b
runs.append((start, cols[-1]))
x0, x1 = runs[n - 1]
rows = np.where(ink[:, x0:x1 + 1].any(axis=1))[0]
y0, y1 = rows[0], rows[-1]
head_y1 = y0 + int((y1 - y0) * 0.46)                               # head and quills only, down to the chin
crop = im[y0:head_y1 + 1, x0:x1 + 1].copy()
h, w = crop.shape[:2]
white = (crop[..., :3].min(axis=2) >= 235) | (crop[..., 3] == 0)
bg = np.zeros((h, w), bool)
stack = [(0, x) for x in range(w)] + [(h - 1, x) for x in range(w)] + [(y, 0) for y in range(h)] + [(y, w - 1) for y in range(h)]
while stack:
    y, x = stack.pop()
    if 0 <= y < h and 0 <= x < w and white[y, x] and not bg[y, x]:
        bg[y, x] = True
        stack += [(y + 1, x), (y - 1, x), (y, x + 1), (y, x - 1)]
crop[..., 3] = np.where(bg, 0, 255)
head = Image.fromarray(crop.astype(np.uint8), "RGBA")
head = head.crop(head.getbbox())
side = max(head.size)
sq = Image.new("RGBA", (side, side), (0, 0, 0, 0))
sq.paste(head, ((side - head.width) // 2, side - head.height), head)
os.makedirs(out, exist_ok=True)
sq.resize((24, 24), Image.BOX).save(os.path.join(out, "stc.png"))
sq.resize((96, 96), Image.NEAREST).save(os.path.join(out, "stc_preview.png"))
print("sprite", n, "box", (x0, y0, x1, y1), "head", head.size, "->", os.path.join(out, "stc.png"))

# select-screen icon (v75): Melee's own icon frame and name plate (taken from Fox's icon, which the user's ISO has), the
# face area cleared, the Sonic 2 head inside and "SONIC" on the name plate
fox = os.path.join(out, "icon_Fox.png")
if os.path.exists(fox):
    from PIL import ImageDraw, ImageFont
    ic = np.asarray(Image.open(fox).convert("RGBA")).copy()
    ic[3:42, 3:61] = 0                                                  # face area -> transparent
    for y in range(43, 52):                                             # name plate: repeat its text-free left column
        ic[y, 3:61] = ic[y, 3]
    base = Image.fromarray(ic, "RGBA")
    hd = head.copy()
    s_ = min(56 / hd.width, 38 / hd.height)
    hd = hd.resize((max(1, int(hd.width * s_)), max(1, int(hd.height * s_))), Image.LANCZOS)
    base.paste(hd, (3 + (58 - hd.width) // 2, 42 - hd.height), hd)
    dr = ImageDraw.Draw(base)
    try:
        font = ImageFont.truetype("C:/Windows/Fonts/arialbd.ttf", 10)
    except Exception:
        font = ImageFont.load_default()
    text = "S O N I C"
    tw = dr.textlength(text, font=font)
    dr.text((32 - tw / 2, 42), text, fill=(255, 255, 255, 255), font=font)
    base.save(os.path.join(out, "css_icon.png"))
    print("select-screen icon ->", os.path.join(out, "css_icon.png"))
