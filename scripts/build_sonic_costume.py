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
# Matches crashed at load whenever one bone carried 5 or more parts (found by elimination: head had 6, each
# shoe 5; variants with at most 4 per bone load). So some parts sit on a rigid child bone of their bone:
# eye whites and pupils on the two face bones under the head, toe caps on the toe bones.
NODE_ATTACH = {"023": 40, "017": 41, "021": 41, "053": 17, "063": 11}
groups = {}   # (image, diffuse) -> list of corner dicts (3 per triangle)
obj_lines, vcount = [], 0
for part in data["parts"]:
    lin, t, bone = maps[part["node"]]
    bone = NODE_ATTACH.get(part["node"], bone)
    nlin = np.linalg.inv(lin).T
    wb_inv = np.linalg.inv(W[bone])
    rb_t = W[bone][:3, :3].T
    for tri in part["tris"]:
        m = data["materials"][tri["m"]]
        key = (m["image"], tuple(round(c, 4) for c in m["saio"]["diffuse"][:3]), bool(m["saio"]["clamp_u"]), bool(m["saio"]["clamp_v"]))
        # the visibility table has room for 44 parts: fold the 2-triangle grey fur patch on the head into the blue fur
        if key[0] == "alltx_dwhite":       # plain white, same as the glove white: one part instead of two
            key = ("stx_eye00", key[1], True, True)
        if key[0] == "stx_btest1" and key[1] != (0.2, 0.2, 1.0):
            key = ("stx_btest1", (0.2, 0.2, 1.0), key[2], key[3])
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

# Rigid parts the way Melee's own files store them: each part is a DOBJ on its bone, vertices in bone space,
# no envelope/skinning data. (Binding through single-weight envelopes on the root crashed matches depending
# on load order.)
from HSDRaw.Common import JOBJ_FLAG  # noqa: E402

gen = POBJ_Generator()
attrs = Array[GXAttribName]([GXAttribName.GX_VA_POS, GXAttribName.GX_VA_NRM, GXAttribName.GX_VA_TEX0])
mobj_cache = {}


def make_mobj(key):
    image, dif, clamp_u, clamp_v = key
    if key not in mobj_cache:
        img = Image.open(os.path.join(tex_dir, image + ".png")).convert("RGBA")
        px = np.array(img, dtype=np.float32)
        px[..., :3] *= np.array(dif, dtype=np.float32)       # SA1 multiplies the texture by the material colour
        px = np.clip(px, 0, 255).astype(np.uint8)
        bgra = px[..., [2, 1, 0, 3]].copy()
        bgra[..., 3] = 255                                    # everything renders opaque
        mobj = clone(template_dobj.Mobj)
        tobj = mobj.Textures
        tobj.Next = None
        tobj.EncodeImageData(Array[Byte](bgra.tobytes()), img.width, img.height, GXTexFmt.RGB565, GXTlutFmt.IA8)
        tobj.WrapS = GXWrapMode.CLAMP if clamp_u else GXWrapMode.REPEAT
        tobj.WrapT = GXWrapMode.CLAMP if clamp_v else GXWrapMode.REPEAT
        mobj_cache[key] = mobj
        return mobj
    return clone(mobj_cache[key])


by_bone = {}
for key, corners in groups.items():
    for i in range(0, len(corners), 3):
        tri = corners[i:i + 3]
        by_bone.setdefault(tri[0]["bone"], {}).setdefault(key, []).extend(tri)
SKIP_BONES = [int(x) for x in os.environ.get('SKIP_BONES', '').split(',') if x]   # diagnostic only
for sb in SKIP_BONES:
    by_bone.pop(sb, None)
dobj_count = 0
for bone in sorted(by_bone):            # joint order = the order the game numbers model parts
    prev = None
    for key, corners in sorted(by_bone[bone].items(), key=lambda kv: -len(kv[1])):
        verts = List[GX_Vertex]()
        for c in corners:
            v = GX_Vertex()
            v.POS = GXVector3(float(c["pl"][0]), float(c["pl"][1]), float(c["pl"][2]))
            v.NRM = GXVector3(float(c["nl"][0]), float(c["nl"][1]), float(c["nl"][2]))
            v.TEX0 = GXVector2(float(c["uv"][0]), float(c["uv"][1]))
            verts.Add(v)
        dobj = HSD_DOBJ()
        dobj.Mobj = make_mobj(key)
        dobj.Pobj = gen.CreatePOBJsFromTriangleList(verts, attrs, None)
        if prev is None:
            joints[bone][0].Dobj = dobj
        else:
            prev.Next = dobj
        prev = dobj
        dobj_count += 1
    j = joints[bone][0]
    j.Flags = j.Flags | JOBJ_FLAG.LIGHTING | JOBJ_FLAG.OPA
    par = joints[bone][1]
    while par >= 0:
        joints[par][0].Flags = joints[par][0].Flags | JOBJ_FLAG.ROOT_OPA
        par = joints[par][1]
    print(f"  bone {bone:2}: {len(by_bone[bone])} parts")
gen.SaveChanges()
f.Save(out_dat)
print("saved", out_dat, os.path.getsize(out_dat), "bytes | dobjs", dobj_count)
