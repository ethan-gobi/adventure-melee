"""Build Sonic's Melee costume model: SA1 Dreamcast parts bound rigidly to Captain Falcon's skeleton.

Usage: python build_sonic_costume.py <falcon_costume.dat> <sonic_parts.json> <texture_dir> <out_costume.dat> <preview.obj>

v04 approach ("Falcon proportions"): the skeleton is untouched, so every Falcon animation still applies.
Each Sonic part is placed on one Falcon bone; limb segments are stretched along the bone to match its length.
"""
import json
import math
import os
import sys

import numpy as np
from PIL import Image

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from hsd import *  # noqa: E402,F401
from System import Array, Byte, Single  # noqa: E402
from System.Collections.Generic import List  # noqa: E402
from HSDRaw import HSDAccessor  # noqa: E402
from HSDRaw.GX import GX_Vertex, GXVector3, GXVector2, GXAttribName, GXTexFmt, GXTlutFmt, GXWrapMode  # noqa: E402
from HSDRaw.Tools import POBJ_Generator  # noqa: E402

src_dat, parts_json, tex_dir, out_dat, preview_obj = sys.argv[1:6]

# ---------------------------------------------------------------- Falcon skeleton
f = HSDRawFile(src_dat)
root = [r for r in f.Roots if r.Data.GetType().Name == "HSD_JOBJ"][0].Data
joints = jobj_list(root)


def local_matrix(j):
    cx, sx, cy, sy, cz, sz = math.cos(j.RX), math.sin(j.RX), math.cos(j.RY), math.sin(j.RY), math.cos(j.RZ), math.sin(j.RZ)
    rx = np.array([[1, 0, 0], [0, cx, -sx], [0, sx, cx]])
    ry = np.array([[cy, 0, sy], [0, 1, 0], [-sy, 0, cy]])
    rz = np.array([[cz, -sz, 0], [sz, cz, 0], [0, 0, 1]])
    m = np.eye(4)
    m[:3, :3] = rz @ ry @ rx @ np.diag([j.SX, j.SY, j.SZ])
    m[:3, 3] = [j.TX, j.TY, j.TZ]
    return m


# ---------------------------------------------------------------- v05: Sonic proportions
import sonic_proportions as sp  # noqa: E402

data = json.load(open(parts_json))
K, factors, G = sp.compute(joints, None, data)
for b, fct in factors.items():
    j = joints[b][0]
    j.TX, j.TY, j.TZ = j.TX * fct, j.TY * fct, j.TZ * fct
with open(os.path.splitext(out_dat)[0] + "_bone_factors.json", "w") as fo:
    json.dump({str(k): v for k, v in factors.items()}, fo, indent=1)

W = []
for j, parent, _ in joints:
    W.append(local_matrix(j) if parent < 0 else W[parent] @ local_matrix(j))
bone_pos = [w[:3, 3].copy() for w in W]
S = sp.S
node = {k: G(v["pos"]) for k, v in data["nodes"].items()}
FWD = np.array([0.0, 0.0, 1.0])
UP = np.array([0.0, 1.0, 0.0])


def frame(d):
    d = d / np.linalg.norm(d)
    ref = FWD if abs(d @ FWD) < 0.9 else UP
    fwd = ref - (ref @ d) * d
    fwd /= np.linalg.norm(fwd)
    return np.column_stack([d, fwd, np.cross(d, fwd)])


def place(lin, anchor_src, anchor_dst):
    return lin, anchor_dst - lin @ anchor_src


def Sk(n):
    return S(data["nodes"][n]["pos"])


IDENT = np.eye(3) * K
maps = {}  # sonic node id -> (linear 3x3, translation, falcon bone index)

# body and tail: global placement (soles on the floor), bound to bust / hip
for n_, bone in (("010", 19), ("069", 4)):
    maps[n_] = (*place(IDENT, S([0, 0, 0]), G([0, 0, 0])), bone)
# head, eyes, pupils: neck node -> neck bone position, bound to the head bone
# Falcon's animations tilt the head forward ~23 deg (median over common moves), which hides Sonic's face
# under his big head, so the head geometry is pre-tilted back by HEAD_TILT about the neck.
HEAD_TILT = math.radians(-20.0)
RX = np.array([[1, 0, 0], [0, math.cos(HEAD_TILT), -math.sin(HEAD_TILT)], [0, math.sin(HEAD_TILT), math.cos(HEAD_TILT)]])
for n_ in ("022", "023", "017", "021"):
    maps[n_] = (*place(RX @ IDENT, Sk("022"), bone_pos[38]), 39)


def limb(chain, segs, end_parts, end_mode):
    (a, b_, d), (fa, fb, fd) = chain
    rot = None
    for parts_, (s0, s1), (b0, b1) in ((segs[0], (a, b_), (fa, fb)), (segs[1], (b_, d), (fb, fd))):
        fsv, ffv = frame(Sk(s1) - Sk(s0)), frame(bone_pos[b1] - bone_pos[b0])
        axial = np.linalg.norm(bone_pos[b1] - bone_pos[b0]) / (K * np.linalg.norm(Sk(s1) - Sk(s0)))
        lin = ffv @ np.diag([axial, 1.0, 1.0]) @ fsv.T * K
        for n_ in parts_:
            maps[n_] = (*place(lin, Sk(s0), bone_pos[b0]), b0)
        rot = ffv @ fsv.T
    if end_mode == "hand":
        for n_ in end_parts:
            maps[n_] = (*place(rot * K, Sk(d), bone_pos[fd]), fd)
    else:  # shoe: unrotated, ankle on the foot bone, then moved so the sole touches the floor
        lin, t = place(IDENT, Sk(d), bone_pos[fd])
        sole = min((lin @ S(c["p"]) + t)[1] for p in data["parts"] if p["node"] in end_parts for tr in p["tris"] for c in tr["v"])
        t = t - np.array([0.0, sole, 0.0])
        for n_ in end_parts:
            maps[n_] = (lin, t, fd)


limb((("025", "026", "028"), (45, 46, 47)), (["034"], ["033", "029"]), ["030", "031", "032"], "hand")
limb((("036", "037", "039"), (23, 24, 25)), (["045"], ["044", "040"]), ["041", "042", "043"], "hand")
limb((("047", "048", "050"), (13, 14, 16)), (["055"], ["054", "051"]), ["052", "053"], "shoe")
limb((("057", "058", "060"), (7, 8, 10)), (["065"], ["064", "061"]), ["062", "063"], "shoe")

for n_, b in (("057", 7), ("058", 8), ("060", 10), ("036", 23), ("037", 24), ("039", 25), ("022", 38)):
    print(f"  Sonic joint {n_} at {np.round(node[n_], 2)} vs bone {b} {np.round(bone_pos[b], 2)} (gap {np.linalg.norm(node[n_] - bone_pos[b]):.2f})")
missing = [p["node"] for p in data["parts"] if p["node"] not in maps]
if missing:
    raise SystemExit(f"unmapped Sonic parts: {missing}")

# ---------------------------------------------------------------- transform every triangle corner
groups = {}   # (image, diffuse) -> list of corner dicts (3 per triangle)
obj_lines, vcount = [], 0
for part in data["parts"]:
    lin, t, bone = maps[part["node"]]
    nlin = np.linalg.inv(lin).T
    wb_inv = np.linalg.inv(W[bone])
    rb_t = W[bone][:3, :3].T
    for tri in part["tris"]:
        m = data["materials"][tri["m"]]
        key = (m["image"], tuple(round(c, 4) for c in m["saio"]["diffuse"][:3]), bool(m["saio"]["clamp_u"]), bool(m["saio"]["clamp_v"]))
        for c in tri["v"]:
            pw = lin @ S(c["p"]) + t
            nw = nlin @ S(c["n"])
            nw /= np.linalg.norm(nw)
            pl = (wb_inv @ np.append(pw, 1.0))[:3]
            nl = rb_t @ nw
            groups.setdefault(key, []).append({"pl": pl, "nl": nl, "uv": (c["uv"][0], 1.0 - c["uv"][1]), "bone": bone})
            obj_lines.append(f"v {pw[0]:.4f} {pw[1]:.4f} {pw[2]:.4f}")
            vcount += 1
        obj_lines.append(f"f {vcount - 2} {vcount - 1} {vcount}")
bound_dump = {"joints": [[j.TX, j.TY, j.TZ, j.RX, j.RY, j.RZ, j.SX, j.SY, j.SZ, p] for j, p, _ in joints], "groups": [],
              "K": K, "maps": {n_: {"lin": np.asarray(m[0]).tolist(), "t": np.asarray(m[1]).tolist(), "bone": int(m[2])} for n_, m in maps.items()}}
for (image, dif, cu, cv), corners in groups.items():
    bound_dump["groups"].append({"image": image, "dif": list(dif), "c": [[c["bone"], *[float(x) for x in c["pl"]], float(c["uv"][0]), float(c["uv"][1])] for c in corners]})
with open(os.path.splitext(out_dat)[0] + "_bound.json", "w") as fo:
    json.dump(bound_dump, fo)
with open(preview_obj, "w") as fo:
    fo.write("\n".join(obj_lines) + "\n")
allp = np.array([[float(x) for x in l.split()[1:]] for l in obj_lines if l.startswith("v ")])
print("world bounds min", np.round(allp.min(0), 2), "max", np.round(allp.max(0), 2), "| triangles", vcount // 3, "| material groups", len(groups))

# ---------------------------------------------------------------- build HSD objects
# templates: a plain DIFFUSE|TEX0 material from one of Falcon's own rigid parts
template_dobj = joints[5][0].Dobj
deep = HSDAccessor.DeepClone.__overloads__ if hasattr(HSDAccessor.DeepClone, "__overloads__") else None


def clone(o):
    return HSDAccessor.DeepClone[type(o)](o)


for j, _, _ in joints:
    j.Dobj = None

gen = POBJ_Generator()
attrs = Array[GXAttribName]([GXAttribName.GX_VA_PNMTXIDX, GXAttribName.GX_VA_POS, GXAttribName.GX_VA_NRM, GXAttribName.GX_VA_TEX0])
first = prev = None
dobj_count = 0
for (image, dif, clamp_u, clamp_v), corners in sorted(groups.items(), key=lambda kv: -len(kv[1])):
    img = Image.open(os.path.join(tex_dir, image + ".png")).convert("RGBA")
    if img.width < 128:                                   # v35: smoother, sharper-edged textures (4x upscale)
        img = img.resize((img.width * 4, img.height * 4), Image.LANCZOS)
    px = np.array(img, dtype=np.float32)
    # v25: the texture is used as it is. Multiplying by the SA1 material colour made the iris black and tinted
    # the already-coloured skin and sole textures (orange skin, dark red soles).
    if image in ('stx_btest1', 'stx_head'):
        px[..., :3] *= 1.35                                # SA1's quill texture is very dark under Melee's lighting
    px = np.clip(px, 0, 255).astype(np.uint8)
    bgra = px[..., [2, 1, 0, 3]].copy()
    bgra[..., 3] = 255                                    # v04 renders everything opaque
    mobj = clone(template_dobj.Mobj)
    for ch in 'RGB':
        setattr(mobj.Material, 'DIF_' + ch, 255)
        setattr(mobj.Material, 'AMB_' + ch, 200)
    tobj = mobj.Textures
    tobj.Next = None
    tobj.EncodeImageData(Array[Byte](bgra.tobytes()), img.width, img.height, GXTexFmt.RGB565, GXTlutFmt.IA8)
    tobj.WrapS = GXWrapMode.CLAMP if clamp_u else GXWrapMode.REPEAT
    tobj.WrapT = GXWrapMode.CLAMP if clamp_v else GXWrapMode.REPEAT
    verts, jl, wl = List[GX_Vertex](), List[Array[HSD_JOBJ]](), List[Array[Single]]()
    use = corners
    if image in ('stx_eye00', 'stx_eye2'):
        # SA1 layers the eye whites and irises exactly on the head surface. In Melee they flickered through each other
        # and the irises were buried. Lift them away from the real centre of the head (world space), irises furthest.
        HEAD = (38, 39, 40, 41)
        wp = lambda c: (W[c["bone"]] @ np.append(c["pl"], 1.0))[:3]   # noqa: E731
        centre = np.mean([wp(c) for cs in groups.values() for c in cs if c["bone"] in HEAD], axis=0)
        amount = 0.09 if image == 'stx_eye2' else 0.0   # v70: 0.06 -> 0.09      # lifting the whites (v27-v30) only let more of the blue brow cover them
        eyes = np.array([wp(c) for c in groups[next(k for k in groups if k[0] == 'stx_eye00')] if c["bone"] in HEAD])
        pivot = eyes.mean(axis=0) + np.array([0.0, 0.0, -1.3])        # inside the head, behind the eyes
        TURN = math.radians(0)    # v68: back to 0 (v66 14 looked creepy from the front, user)                                        # Melee's camera is side-on: turn each iris toward its own side
        use = []
        for c in corners:
            if c["bone"] not in HEAD:
                use.append(c)
                continue
            p_ = wp(c)
            if image == 'stx_eye2':
                sgn = 1.0 if p_[0] > pivot[0] else -1.0
                side = np.array([wp(q) for q in corners if (wp(q)[0] > pivot[0]) == (p_[0] > pivot[0])]).mean(axis=0)
                p_ = side + (p_ - side) * 1.18   # v70: 1.0 -> 1.18, not turned (user: more visible from the side, same place)                         # each iris 20% larger about its own centre
                ca, sa_ = math.cos(sgn * TURN), math.sin(sgn * TURN)
                d = p_ - pivot
                p_ = pivot + np.array([ca * d[0] + sa_ * d[2], d[1], -sa_ * d[0] + ca * d[2]])
                o = p_ - pivot
            else:
                o = p_ - pivot                                   # away from the inside of the eye bulge, close to the surface normal
            o = o / np.linalg.norm(o)
            p_ = p_ + amount * o
            Wi = np.linalg.inv(W[c["bone"]])
            use.append({"pl": (Wi @ np.append(p_, 1.0))[:3], "nl": W[c["bone"]][:3, :3].T @ o if image == 'stx_eye2' else c["nl"], "uv": c["uv"], "bone": c["bone"]})
        if image == 'stx_eye2':
            for n in range(0, len(corners), 3):
                use += [use[n], use[n + 2], use[n + 1]]              # visible from both sides
    for c in use:
        v = GX_Vertex()
        v.POS = GXVector3(float(c["pl"][0]), float(c["pl"][1]), float(c["pl"][2]))
        v.NRM = GXVector3(float(c["nl"][0]), float(c["nl"][1]), float(c["nl"][2]))
        v.TEX0 = GXVector2(float(c["uv"][0]), float(c["uv"][1]))
        verts.Add(v)
        jl.Add(Array[HSD_JOBJ]([joints[c["bone"]][0]]))
        wl.Add(Array[Single]([1.0]))
    dobj = HSD_DOBJ()
    dobj.Mobj = mobj
    dobj.Pobj = gen.CreatePOBJsFromTriangleList(verts, attrs, jl, wl)
    if first is None:
        first = dobj
    else:
        prev.Next = dobj
    prev = dobj
    dobj_count += 1
    print(f"  dobj {dobj_count - 1:2}: {image:14} dif={dif} tris={len(corners) // 3} tex={img.width}x{img.height}")
# ================================================================ extra parts (v47). DOBJ order after the 18 body groups:
#   18 mouth smile | 19 spin ball | 20 Chaos Emerald | 21 emerald glint | 22 light-speed trail | 23 mouth open
from PIL import ImageFilter, ImageEnhance


def flat(bgr, n=8):
    a_ = np.zeros((n, n, 4), dtype=np.uint8)
    a_[..., 0], a_[..., 1], a_[..., 2], a_[..., 3] = bgr[0], bgr[1], bgr[2], 255
    return a_


def make_dobj(corner_list, bgra, amb=200):
    """corner_list: [(pos, normal, (u, v), bone)] three per triangle."""
    global prev, dobj_count
    mobj_ = clone(template_dobj.Mobj)
    for ch in 'RGB':
        setattr(mobj_.Material, 'DIF_' + ch, 255)
        setattr(mobj_.Material, 'AMB_' + ch, amb)
    t_ = mobj_.Textures
    t_.Next = None
    t_.EncodeImageData(Array[Byte](np.ascontiguousarray(bgra).tobytes()), bgra.shape[1], bgra.shape[0], GXTexFmt.RGB565, GXTlutFmt.IA8)
    t_.WrapS = GXWrapMode.CLAMP
    t_.WrapT = GXWrapMode.CLAMP
    verts_, jl_, wl_ = List[GX_Vertex](), List[Array[HSD_JOBJ]](), List[Array[Single]]()
    for p_, n_, uv_, bone_ in corner_list:
        v = GX_Vertex()
        v.POS = GXVector3(float(p_[0]), float(p_[1]), float(p_[2]))
        v.NRM = GXVector3(float(n_[0]), float(n_[1]), float(n_[2]))
        v.TEX0 = GXVector2(float(uv_[0]), float(uv_[1]))
        verts_.Add(v)
        jl_.Add(Array[HSD_JOBJ]([joints[bone_][0]]))
        wl_.Add(Array[Single]([1.0]))
    d_ = HSD_DOBJ()
    d_.Mobj = mobj_
    d_.Pobj = gen.CreatePOBJsFromTriangleList(verts_, attrs, jl_, wl_)
    prev.Next = d_
    prev = d_
    dobj_count += 1
    return d_


def tri(pts, bone, uv=(0.5, 0.5)):
    n_ = np.cross(pts[1] - pts[0], pts[2] - pts[0])
    n_ = n_ / (np.linalg.norm(n_) + 1e-9)
    return [(q, n_, uv, bone) for q in pts]


# ---- 18: mouth (closed smile) and 23: open mouth. SA1 keeps Sonic's mouth on a separate head model, so this model has none.
# Both are laid onto the real muzzle surface: every point is cast straight back onto the head's skin triangles and lifted a
# hair off it, so the mouth sits under the nose on the muzzle front and follows its curve (v49; v47/v48 floated in front).
HEADB = 39
Wh, Whi = W[HEADB], np.linalg.inv(W[HEADB])
skin = []
for k_, cs in groups.items():
    if k_[0] in ('stx_hada', 'stx_hoho'):
        for n in range(0, len(cs) - 2, 3):
            if all(cs[n + j]["bone"] == HEADB for j in range(3)):
                skin.append([(Wh @ np.append(cs[n + j]["pl"], 1.0))[:3] for j in range(3)])
skin = np.array(skin)


ZC, TM = -0.3, math.radians(30)         # v57: muzzle axis (x=0, z=ZC); the mouth wraps from -TM to +TM around it
MY, MUP = 11.6, 0.22                    # v61 (user: "mouth way too big"): wrap 60 -> 30 deg, corners 0.5 -> 0.22, centre height, how far the corners turn up at the sides
HW0, HW1, OPEN = 0.045, 0.06, 0.32     # v61: 0.06/0.11/0.75 -> 0.045/0.06/0.32; line half thickness at the front and at the corners; open-mouth depth


def onface(theta, y, lift=0.13):
    """outer skin point at height y, angle theta around the muzzle axis (0 = straight ahead), pushed out along the
    surface normal. v57: rays come in radially, so the mouth wraps round the side of the muzzle where Melee's side-on
    camera sees it (v49-v56 cast straight back, so from the side the mouth was a dot)."""
    d = np.array([-math.sin(theta), 0.0, -math.cos(theta)])
    o = np.array([0.0, y, ZC]) - 6.0 * d
    best = None
    for t in skin:
        e1, e2 = t[1] - t[0], t[2] - t[0]
        pv = np.cross(d, e2); det = e1 @ pv
        if abs(det) < 1e-9:
            continue
        sv = o - t[0]; u = (sv @ pv) / det
        if u < 0 or u > 1:
            continue
        qv = np.cross(sv, e1); v = (d @ qv) / det
        if v < 0 or u + v > 1:
            continue
        tt = (e2 @ qv) / det
        if tt > 0 and (best is None or tt < best[0]):
            nn = np.cross(e1, e2); nn = nn / np.linalg.norm(nn)
            best = (tt, nn if nn @ d < 0 else -nn)
    if best is None:
        raise SystemExit(f"mouth point ({math.degrees(theta):.0f} deg, {y:.2f}) misses the muzzle")
    return o + best[0] * d + lift * best[1], best[1]


_s = lambda q: q / TM                                       # noqa: E731
smile_y = lambda q: MY + MUP * _s(q) ** 2                   # noqa: E731
_hw = lambda q: HW0 + (HW1 - HW0) * _s(q) ** 2              # noqa: E731
_depth = lambda q: OPEN * math.cos(0.5 * math.pi * _s(q)) ** 1.3   # noqa: E731


def band(top, bot, lo=-TM, hi=TM, cols=24, rows=1, lift=0.13):
    out = []
    for i in range(cols):
        for r in range(rows):
            pts = []
            for (qi, rf) in ((i, r), (i, r + 1), (i + 1, r + 1), (i + 1, r)):
                q = lo + (hi - lo) * qi / cols
                y = top(q) + (bot(q) - top(q)) * rf / rows
                pw, nw = onface(q, y, lift)
                pts.append(((Whi @ np.append(pw, 1.0))[:3], Wh[:3, :3].T @ nw))
            for a_, b_, c_ in ((0, 1, 2), (0, 2, 3)):
                out += [(pts[k][0], pts[k][1], (0.5, 0.5), HEADB) for k in (a_, b_, c_)]
    return out


mcorn = band(lambda q: smile_y(q) + _hw(q), lambda q: smile_y(q) - _hw(q))
make_dobj(mcorn, flat((25, 20, 45)))
print(f"  dobj {dobj_count - 1:2}: mouth (smile), {len(mcorn) // 3} triangles, wraps +-{math.degrees(TM):.0f} deg round the muzzle")
# open mouth (part 23): dark red, deepest at the front and closing toward the corners, with a tongue; it sits in front
# of the smile, which still shows at the corners
ocorn = band(lambda q: smile_y(q) + _hw(q), lambda q: smile_y(q) - _hw(q) - _depth(q), -0.75 * TM, 0.75 * TM, cols=18, rows=3, lift=0.19)
tcorn = band(lambda q: smile_y(q) - _hw(q) - 0.55 * _depth(q), lambda q: smile_y(q) - _hw(q) - 0.95 * _depth(q),
             -0.4 * TM, 0.4 * TM, cols=10, rows=2, lift=0.21)

# ---- 19: spin ball (SA1 spin sprite, upscaled)
BALL_R, BALL_C = 4.5, np.array([0.0, 2.0, 1.2])
img = Image.open(os.path.join(tex_dir, "stx_newspin.png")).convert("RGB").resize((256, 256), Image.BICUBIC)
img = ImageEnhance.Contrast(img.filter(ImageFilter.UnsharpMask(3, 120, 2))).enhance(1.15).convert("RGBA")
bgra = np.array(img, dtype=np.uint8)[..., [2, 1, 0, 3]].copy()
bgra[..., 3] = 255
LAT, LON = 10, 18
def sph(i, j):   # noqa: E302
    th, ph = math.pi * i / LAT, 2 * math.pi * j / LON
    return np.array([math.cos(th), math.sin(th) * math.cos(ph), math.sin(th) * math.sin(ph)])
bc = []
for i in range(LAT):
    for j in range(LON):
        quad = [sph(i, j), sph(i + 1, j), sph(i + 1, j + 1), sph(i, j + 1)]
        for t3 in ((0, 1, 2), (0, 2, 3)):
            pts = [quad[k] for k in t3]
            if np.linalg.norm(np.cross(pts[1] - pts[0], pts[2] - pts[0])) < 1e-9:
                continue
            bc += [(BALL_C + BALL_R * n_, n_, (0.5 + 0.47 * n_[2], 0.5 - 0.47 * n_[1]), 2) for n_ in pts]
make_dobj(bc, bgra)
print(f"  dobj {dobj_count - 1:2}: spin ball, {len(bc) // 3} triangles")

# ---- 20: Chaos Emerald on the prop bone 62 (centred, pointing forward), own facet texture
hand = np.array([c["pl"] for cs in groups.values() for c in cs if c["bone"] == 47])
ax_ = hand.mean(axis=0); ax_ = ax_ / np.linalg.norm(ax_)
tipd = float((hand @ ax_).max())
json.dump({"bone": 47, "centre": [float(x) for x in ax_ * (tipd + 1.4)]}, open(os.path.join(os.path.dirname(out_dat), "emerald.json"), "w"))
eg = np.zeros((16, 16, 4), dtype=np.uint8)
for yy_ in range(16):
    for xx_ in range(16):
        b_ = 0.75 + 0.45 * ((xx_ // 4) % 2 == 0) + 0.2 * (yy_ / 15.0)
        eg[yy_, xx_] = (int(min(255, 90 * b_)), int(min(255, 230 * b_)), int(min(255, 60 * b_)), 255)
SEG = 8
ring = lambda z, r, k: np.array([r * math.sin(2 * math.pi * k / SEG), r * math.cos(2 * math.pi * k / SEG), z])   # noqa: E731
TABLE, GIRDLE, TIP, BACK = (-1.7, 0.8), (-0.9, 1.45), np.array([0.0, 0.0, 1.9]), np.array([0.0, 0.0, -1.7])
ec = []
for k in range(SEG):
    t0, t1, g0, g1 = ring(*TABLE, k), ring(*TABLE, k + 1), ring(*GIRDLE, k), ring(*GIRDLE, k + 1)
    u = 0.1 + 0.25 * (k % 4)
    ec += tri([BACK, t0, t1], 62, (u, 0.9)) + tri([t0, g0, g1], 62, (u, 0.5)) + tri([t0, g1, t1], 62, (u, 0.5)) + tri([g0, TIP, g1], 62, (u, 0.1))
make_dobj(ec, eg)
print(f"  dobj {dobj_count - 1:2}: chaos emerald, {len(ec) // 3} triangles")

# ---- 21: glint on the emerald: a white four-point star in the plane the side-on camera sees (Y/Z), plus one across it
A3 = lambda *v: np.array(v, dtype=float)   # noqa: E731
sc_ = []
for (long_, short_) in ((A3(0, 3.8, 0), A3(0, 0, 0.5)), (A3(0, 0, 3.8), A3(0, 0.5, 0)), (A3(2.8, 0, 0), A3(0, 0.4, 0)),
                       (A3(0, 1.9, 1.9), A3(0, 0.3, -0.3)), (A3(0, 1.9, -1.9), A3(0, 0.3, 0.3))):   # v52: bigger, plus diagonals
    for off_ in (A3(0.9, 0.5, 0.5), A3(-0.9, 0.5, 0.5)) if long_[0] == 0 else (A3(0, 0.5, 0.5),):
        sc_ += tri([off_ + long_, off_ + short_, off_ - short_], 62) + tri([off_ - long_, off_ - short_, off_ + short_], 62)
make_dobj(sc_, flat((255, 255, 255)), amb=255)   # full ambient: lit white whatever the stage lighting
print(f"  dobj {dobj_count - 1:2}: emerald glint, {len(sc_) // 3} triangles")

# ---- 22: light-speed trail for the Light Dash: a tapering streak behind the prop bone, blue at the body fading to white
tg = np.zeros((8, 32, 4), dtype=np.uint8)
for xx_ in range(32):
    f_ = xx_ / 31.0
    tg[:, xx_] = (255, int(215 + 40 * f_), int(140 + 115 * f_), 255)      # B, G, R: bright blue -> white
tc = []
TSEG, TLEN, TR = 8, 20.0, 2.6
tring = lambda z, r, k: np.array([r * math.sin(2 * math.pi * k / TSEG), r * math.cos(2 * math.pi * k / TSEG) * 1.25, z])   # noqa: E731
for k in range(TSEG):
    a0, a1 = tring(0.0, TR, k), tring(0.0, TR, k + 1)
    m0, m1 = tring(-TLEN * 0.45, TR * 0.6, k), tring(-TLEN * 0.45, TR * 0.6, k + 1)
    tail_ = np.array([0.0, 0.0, -TLEN])
    for pts, us in (([a0, m0, m1], (0.05, 0.5, 0.5)), ([a0, m1, a1], (0.05, 0.5, 0.05)), ([m0, tail_, m1], (0.5, 0.95, 0.5))):
        n_ = np.cross(pts[1] - pts[0], pts[2] - pts[0]); n_ = n_ / (np.linalg.norm(n_) + 1e-9)
        tc += [(q, n_, (u_, 0.5), 62) for q, u_ in zip(pts, us)]
make_dobj(tc, tg)
print(f"  dobj {dobj_count - 1:2}: light-speed trail, {len(tc) // 3} triangles")
mtex = np.zeros((8, 8, 4), dtype=np.uint8)
mtex[:, :4] = (40, 30, 120, 255)                    # BGRA: dark red inside
mtex[:, 4:] = (95, 85, 205, 255)                    # pink tongue
ocorn = [(p_, n_, (0.2, 0.5), b_) for p_, n_, _, b_ in ocorn] + [(p_, n_, (0.8, 0.5), b_) for p_, n_, _, b_ in tcorn]
make_dobj(ocorn, mtex)
print(f"  dobj {dobj_count - 1:2}: mouth (open, with tongue), {len(ocorn) // 3} triangles")

# ---- 24: Super Peel-Out figure-8 (Sonic CD): the red-and-white infinity loop his legs blur into. Two flat ribbons, one over
# each leg, on the prop bone 62. Centred 1.7 above the bone, so with the bone at rest (the fighter's base point) it sits at shoe height.
f8 = np.zeros((8, 32, 4), dtype=np.uint8)
for xx_ in range(32):
    f8[:, xx_] = (255, 255, 255, 255) if (xx_ // 4) % 2 == 1 else (45, 45, 235, 255)      # B, G, R: white / shoe red
FA, FW, FN, FY = 3.6, 0.85, 40, 1.7
def lem(t):   # noqa: E302  lemniscate in the Y/Z plane (what the side-on camera sees)
    d_ = 1 + math.sin(t) ** 2
    return np.array([0.0, FY + FA * math.sin(t) * math.cos(t) / d_, FA * math.cos(t) / d_])
fcorn = []
for xoff in (-0.85, 0.85):
    for k in range(FN):
        t0, t1 = 2 * math.pi * k / FN, 2 * math.pi * (k + 1) / FN
        quad = []
        for t_ in (t0, t1):
            p_ = lem(t_)
            tan = lem(t_ + 0.01) - lem(t_ - 0.01); tan = tan / (np.linalg.norm(tan) + 1e-9)
            nrm = np.array([0.0, -tan[2], tan[1]])
            quad.append((p_ + nrm * FW / 2 + [xoff, 0, 0], p_ - nrm * FW / 2 + [xoff, 0, 0]))
        (a0, b0), (a1, b1) = quad
        u0, u1 = k / FN, (k + 1) / FN
        side_n = np.array([1.0 if xoff > 0 else -1.0, 0.0, 0.0])
        fcorn += [(a0, side_n, (u0, 0.5), 62), (b0, side_n, (u0, 0.5), 62), (b1, side_n, (u1, 0.5), 62),
                  (a0, side_n, (u0, 0.5), 62), (b1, side_n, (u1, 0.5), 62), (a1, side_n, (u1, 0.5), 62)]
make_dobj(fcorn, f8, amb=255)
print(f"  dobj {dobj_count - 1:2}: Peel-Out figure-8, {len(fcorn) // 3} triangles")

# ---- 25: Insta-Shield (Sonic 3): a white crescent that flashes round the spinning ball. On bone 2 with the ball, so it
# whirls with the spin. A 220-degree arc of radius about 6.4, thickest in the middle.
icorn = []
IN, IMAX = 26, math.radians(110)
def ipt(th, r):   # noqa: E302
    return BALL_C + np.array([0.0, r * math.cos(th), r * math.sin(th)])
for k in range(IN):
    th0, th1 = -IMAX + 2 * IMAX * k / IN, -IMAX + 2 * IMAX * (k + 1) / IN
    w0, w1 = 0.06 + 0.6 * (1 - (th0 / IMAX) ** 2), 0.06 + 0.6 * (1 - (th1 / IMAX) ** 2)
    q = [ipt(th0, 6.4 + w0), ipt(th0, 6.4 - w0), ipt(th1, 6.4 - w1), ipt(th1, 6.4 + w1)]
    nx = np.array([1.0, 0.0, 0.0])
    icorn += [(q[0], nx, (0.5, 0.5), 2), (q[1], nx, (0.5, 0.5), 2), (q[2], nx, (0.5, 0.5), 2),
              (q[0], nx, (0.5, 0.5), 2), (q[2], nx, (0.5, 0.5), 2), (q[3], nx, (0.5, 0.5), 2)]
make_dobj(icorn, flat((255, 255, 225)), amb=255)
print(f"  dobj {dobj_count - 1:2}: Insta-Shield, {len(icorn) // 3} triangles")

# ---- 26: eyelids (v64). The eye whites again, lifted in front of the irises, in the fur blue with a dark lash line along
# the bottom edge. Hidden normally; the fighter code shows them for a few frames to blink and keeps them shut while he is
# asleep, dizzy, flinching or knocked down (visibility group 4).
_HEAD = (38, 39, 40, 41)
_ecs = [c for c in groups[next(k for k in groups if k[0] == 'stx_eye00')] if c["bone"] in _HEAD]
_ewp = np.array([(W[c["bone"]] @ np.append(c["pl"], 1.0))[:3] for c in _ecs])
_epiv = _ewp.mean(axis=0) + np.array([0.0, 0.0, -1.3])
_y0, _y1 = _ewp[:, 1].min(), _ewp[:, 1].max()
lid = []
for c, p_ in zip(_ecs, _ewp):
    o = (p_ - _epiv) / np.linalg.norm(p_ - _epiv)
    q = p_ + 0.30 * o                                   # v75: 0.16 -> 0.30 (the 1.18x irises poked through)
    lid.append(((np.linalg.inv(W[c["bone"]]) @ np.append(q, 1.0))[:3], W[c["bone"]][:3, :3].T @ o,
                (0.5, 0.05 + 0.9 * (_y1 - p_[1]) / (_y1 - _y0)), c["bone"]))
_fur = np.array(Image.open(os.path.join(tex_dir, "stx_btest1.png")).convert("RGB"), dtype=float).reshape(-1, 3).mean(axis=0)
ltex = np.zeros((16, 8, 4), dtype=np.uint8)
ltex[..., :3] = [int(_fur[2]), int(_fur[1]), int(_fur[0])]      # BGR
ltex[14:, :, :3] = [70, 20, 10]                                  # lash line (dark navy) along the bottom of the lid
ltex[..., 3] = 255
make_dobj(lid, ltex)
print(f"  dobj {dobj_count - 1:2}: eyelids, {len(lid) // 3} triangles, fur colour {tuple(int(x) for x in _fur)}")

# ---- 27+: Tails (v69), for the air up B: Tails flies down, grabs Sonic's hands and carries him up (Sonic 3). His SA1 model
# (the user's files), posed on frame 4 of his SA1 fly-up animation in Blender (scripts/export_tails_pose.py), placed so his
# hands meet above Sonic's head. Body parts on bone 1 (moves with Sonic, does not tilt with him); the two tails on bone 62
# around their base so the up B animation can spin them like a propeller. One part per texture (32x32 or 64x64).
TAILS_JSON, TAILS_TEX = "C:/adventure-melee/work/tails_fly.json", "C:/adventure-melee/extract/sa1_tex/MILES"
TAILS_HANDS = np.array([0.0, 15.2, 0.6])          # where his hands meet (fighter space)
tails_counts = [0, 0]
if os.path.exists(TAILS_JSON):
    td = json.load(open(TAILS_JSON))
    tri_all = []
    for part_ in td["parts"]:
        imgs_ = {(td["materials"].get(t_["m"]) or {}).get("image") for t_ in part_["tris"]}
        is_tail = "mtx_tail" in imgs_
        for t_ in part_["tris"]:
            img_ = (td["materials"].get(t_["m"]) or {}).get("image") or "mtx_white"
            tri_all.append((is_tail, img_, [(K * S(v_["p"]), S(v_["n"]), (v_["uv"][0], 1.0 - v_["uv"][1])) for v_ in t_["v"]]))
    hands = np.array([q_[0] for tl, im, cs in tri_all if im == "s_testhand" for q_ in cs])
    off = TAILS_HANDS - hands.mean(axis=0)
    tailpts = np.array([q_[0] + off for tl, im, cs in tri_all if tl for q_ in cs])
    pivot = np.array([tailpts[:, 0].mean(), tailpts[:, 1].min(), tailpts[:, 2].mean()])
    json.dump({"pivot": pivot.tolist(), "hands": TAILS_HANDS.tolist()}, open(os.path.splitext(out_dat)[0] + "_tails.json", "w"))
    W1i, W62i = np.linalg.inv(W[1]), np.linalg.inv(W[62])
    for want_tail in (False, True):
        byimg = {}
        for tl, im, cs in tri_all:
            if tl == want_tail:
                byimg.setdefault(im, []).append(cs)
        for im, tris_ in sorted(byimg.items()):
            corners_ = []
            for cs in tris_:
                for pq, nq, uvq in cs:
                    pw_ = pq + off
                    # v75: the whole of Tails on bone 62 around the tail pivot (v69-v74: body on bone 1), so the fighter
                    # code can fly him off when he lets go; the carry animation holds bone 62 at the pivot
                    pl_, bone_ = (W62i @ np.append(pw_ - pivot + W[62][:3, 3], 1.0))[:3], 62
                    corners_.append((pl_, nq / (np.linalg.norm(nq) + 1e-9), uvq, bone_))
            src_ = os.path.join(TAILS_TEX, im + ".png")
            timg = Image.open(src_).convert("RGB") if os.path.exists(src_) else Image.new("RGB", (8, 8), (255, 255, 255))
            ts_ = 64 if max(timg.size) >= 64 else max(8, min(timg.size))
            tb_ = np.array(timg.resize((ts_, ts_), Image.BICUBIC).convert("RGBA"), dtype=np.uint8)[..., [2, 1, 0, 3]].copy()
            tb_[..., 3] = 255
            dd_ = make_dobj(corners_, tb_)
            dd_.Mobj.Textures.WrapS = GXWrapMode.REPEAT
            dd_.Mobj.Textures.WrapT = GXWrapMode.REPEAT
            tails_counts[want_tail] += 1
    print(f"  dobjs {dobj_count - sum(tails_counts):2}-{dobj_count - 1}: Tails, {tails_counts[0]} body + {tails_counts[1]} tail parts; tail pivot {np.round(pivot, 2)}")
# ---- after Tails: Homing Attack lock-on reticle (v70, SA1/SA2): a green ring with four yellow pointers, flat in the plane
# facing the camera (bone 62's local Y-Z plane). The fighter code moves bone 62 onto the target and shows it (group 6).
rtex = np.zeros((8, 8, 4), dtype=np.uint8)
rtex[:, :4, :3] = (60, 230, 40)        # BGR green
rtex[:, 4:, :3] = (40, 220, 255)       # BGR yellow
rtex[..., 3] = 255
rc, RN, RR, RW = [], 32, 4.2, 0.35
nX = np.array([1.0, 0.0, 0.0])
o62 = W[62][:3, 3]
W62i_ = np.linalg.inv(W[62])
loc = lambda q: (W62i_ @ np.append(o62 + q, 1.0))[:3]     # noqa: E731
for k_ in range(RN):
    a0, a1 = 2 * math.pi * k_ / RN, 2 * math.pi * (k_ + 1) / RN
    q = [np.array([0.0, r_ * math.cos(a_), r_ * math.sin(a_)]) for r_, a_ in ((RR + RW, a0), (RR - RW, a0), (RR - RW, a1), (RR + RW, a1))]
    for i3 in ((0, 1, 2), (0, 2, 3)):
        rc += [(loc(q[i]), nX, (0.25, 0.5), 62) for i in i3]
for a_ in (0, 0.5 * math.pi, math.pi, 1.5 * math.pi):        # pointers just outside the ring, aimed at the centre
    tip, base = RR + 0.6, RR + 2.0
    side = np.array([0.0, -math.sin(a_), math.cos(a_)]) * 0.8
    dirv = np.array([0.0, math.cos(a_), math.sin(a_)])
    rc += [(loc(dirv * tip), nX, (0.75, 0.5), 62), (loc(dirv * base + side), nX, (0.75, 0.5), 62), (loc(dirv * base - side), nX, (0.75, 0.5), 62)]
make_dobj(rc, rtex, amb=255)
print(f"  dobj {dobj_count - 1:2}: Homing Attack reticle, {len(rc) // 3} triangles")
# ---- after the reticle: half-closed eyelids (v70), the narrowed attack look of SA1/SA2. The full lid squashed up to the
# top 45% of the eye, a little further out. Group 4 set 2; the fighter code shows it while the mouth is open (attacks).
hl = []
_erad = float(np.max(np.linalg.norm(_ewp - _epiv, axis=1)))
for (pl_, nl_, uv_, b_) in lid:
    pw_ = (W[b_] @ np.append(pl_, 1.0))[:3]
    pw_[1] = _y1 + 0.08 - (_y1 + 0.08 - pw_[1]) * 0.45
    o_ = (pw_ - _epiv) / np.linalg.norm(pw_ - _epiv)
    pw_ = _epiv + o_ * (_erad + 0.34)         # out past the eye bulge and the irises (v75: 0.2 -> 0.34)
    hl.append(((np.linalg.inv(W[b_]) @ np.append(pw_, 1.0))[:3], W[b_][:3, :3].T @ o_, uv_, b_))
make_dobj(hl, ltex)
print(f"  dobj {dobj_count - 1:2}: half eyelids, {len(hl) // 3} triangles")
json.dump({"tails_parts": sum(tails_counts)}, open(os.path.splitext(out_dat)[0] + "_extra.json", "w"))

gen.SaveChanges()
# v32: draw both sides of every polygon. The generator's CULLFRONT flag with these windings made the game draw only
# the far side of each part (hollow face from the front, soles visible through the shoes).
from HSDRaw.Common import POBJ_FLAG
d_ = first
while d_ is not None:
    p_ = d_.Pobj
    while p_ is not None:
        p_.Flags = POBJ_FLAG.ENVELOPE
        p_ = p_.Next
    d_ = d_.Next
root.Dobj = first
f.Save(out_dat)
print("saved", out_dat, os.path.getsize(out_dat), "bytes | dobjs", dobj_count)
