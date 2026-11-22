"""Hand-keyed animations and new hitbox scripts for Sonic (data only).

Poses are written in body space: X = Sonic's left, Y = up, Z = forward.
  root   (pitch, yaw, roll) degrees: pitch > 0 leans/rolls forward, yaw > 0 turns left, roll > 0 leans right
  chest  relative to root; head relative to chest
  thighL/shinL/thighR/shinR   direction the segment points, in the root's frame
  armL/foreL/armR/foreR       direction the segment points, in the chest's frame
  footL/footR  extra toe-down pitch in degrees
  hip    (x, y, z) offset of the hips in units;  ground 0..1: 1 = lowest foot is put on the floor
  move   forward travel of the whole fighter (TransN), units
Only rotations are keyed on the limbs, so parts cannot come apart.
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
import subactions as sa  # noqa: E402
from System.IO import File  # noqa: E402
from System.Collections.Generic import List  # noqa: E402
from HSDRaw.Tools.Melee import FighterAJManager  # noqa: E402
from HSDRaw.Tools import FOBJKey, FOBJFrameEncoder  # noqa: E402
from HSDRaw.Common.Animation import HSD_Track, JointTrackType, GXInterpolationType  # noqa: E402

BOUND = r"C:\adventure-melee\work\v10\PlSnNr_sonic_bound.json"
bd = json.load(open(BOUND))
rest = [np.array(j[:9], dtype=float) for j in bd["joints"]]
parent = [j[9] for j in bd["joints"]]
NB = len(rest)


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


def Rx(d):
    a = math.radians(d); c, s = math.cos(a), math.sin(a)
    return np.array([[1, 0, 0], [0, c, -s], [0, s, c]])


def Ry(d):
    a = math.radians(d); c, s = math.cos(a), math.sin(a)
    return np.array([[c, 0, s], [0, 1, 0], [-s, 0, c]])


def Rz(d):
    a = math.radians(d); c, s = math.cos(a), math.sin(a)
    return np.array([[c, -s, 0], [s, c, 0], [0, 0, 1]])


def eul(e):
    return Ry(e[1]) @ Rx(e[0]) @ Rz(e[2])


def unit(v):
    v = np.array(v, dtype=float)
    n = np.linalg.norm(v)
    return v / n if n > 1e-9 else np.array([0.0, -1.0, 0.0])


def arc(a, b):
    """Shortest rotation taking unit vector a to unit vector b."""
    a, b = unit(a), unit(b)
    v = np.cross(a, b)
    c = float(np.dot(a, b))
    if c < -0.9999:
        ax = unit(np.cross(a, [1.0, 0, 0])) if abs(a[0]) < 0.9 else unit(np.cross(a, [0, 0, 1.0]))
        K = np.array([[0, -ax[2], ax[1]], [ax[2], 0, -ax[0]], [-ax[1], ax[0], 0]])
        return np.eye(3) + 2 * K @ K
    K = np.array([[0, -v[2], v[1]], [v[2], 0, -v[0]], [-v[1], v[0], 0]])
    return np.eye(3) + K + K @ K / (1 + c)


def euler_zyx(R):
    ry = math.asin(max(-1.0, min(1.0, -R[2, 0])))
    return math.atan2(R[2, 1], R[2, 2]), ry, math.atan2(R[1, 0], R[0, 0])


LEGS = {"L": (7, 8, 10), "R": (13, 14, 16)}
ARMS = {"L": (23, 24, 25), "R": (45, 46, 47)}
RD = {}
for s_, (th, sh, ft) in LEGS.items():
    RD["thigh" + s_] = unit(rest_W[sh][:3, 3] - rest_W[th][:3, 3])
    RD["shin" + s_] = unit(rest_W[sh + 1][:3, 3] - rest_W[sh][:3, 3])
for s_, (a, f, h) in ARMS.items():
    RD["arm" + s_] = unit(rest_W[f][:3, 3] - rest_W[a][:3, 3])
    RD["fore" + s_] = unit(rest_W[h][:3, 3] - rest_W[f][:3, 3])

VEC_KEYS = list(RD.keys())
DEFAULT = {"root": (0, 0, 0), "chest": (0, 0, 0), "head": (0, 0, 0), "hip": (0, 0, 0), "pivot": (0, 0, 0), "ground": 1.0, "move": 0.0,
           "footL": 0.0, "footR": 0.0,
           "thighL": (0.10, -1, 0.22), "shinL": (0.06, -1, -0.22), "thighR": (-0.10, -1, -0.05), "shinR": (-0.06, -1, -0.30),
           "armL": (0.45, -1, -0.10), "foreL": (0.30, -1, 0.45), "armR": (-0.45, -1, -0.15), "foreR": (-0.30, -1, 0.40)}


def P(base=None, **kw):
    p = dict(DEFAULT if base is None else base)
    p.update(kw)
    return p


def mirror(p):
    """Swap left and right."""
    q = dict(p)
    for k in ("thigh", "shin", "arm", "fore"):
        for a, b in (("L", "R"), ("R", "L")):
            v = p[k + a]
            q[k + b] = (-v[0], v[1], v[2])
    q["footL"], q["footR"] = p["footR"], p["footL"]
    for k in ("root", "chest", "head"):
        q[k] = (p[k][0], -p[k][1], -p[k][2])
    q["hip"] = (-p["hip"][0], p["hip"][1], p["hip"][2])
    return q


def lerp_pose(a, b, t):
    out = {}
    for k in a:
        va, vb = np.array(a[k], dtype=float), np.array(b[k], dtype=float)
        v = va + (vb - va) * t
        out[k] = unit(v) if k in RD else v
    return out


EASE = {"lin": lambda t: t, "io": lambda t: t * t * (3 - 2 * t), "in": lambda t: t * t, "out": lambda t: 1 - (1 - t) * (1 - t)}


def sample(keys, T):
    """keys: [(frame, pose[, ease])] sorted -> list of T+1 poses."""
    out = []
    for f in range(T + 1):
        if f <= keys[0][0]:
            out.append(lerp_pose(keys[0][1], keys[0][1], 0)); continue
        if f >= keys[-1][0]:
            out.append(lerp_pose(keys[-1][1], keys[-1][1], 0)); continue
        for k in range(len(keys) - 1):
            f0, f1 = keys[k][0], keys[k + 1][0]
            if f0 <= f <= f1:
                e = keys[k + 1][2] if len(keys[k + 1]) > 2 else "io"
                out.append(lerp_pose(keys[k][1], keys[k + 1][1], EASE[e]((f - f0) / (f1 - f0))))
                break
    return out


def solve(p):
    """pose -> (world matrices, {bone: (tx,ty,tz,rx,ry,rz)})"""
    Rr = eul(p["root"])
    Dc = Rr @ eul(p["chest"])
    D = {2: Rr, 19: Dc, 39: Dc @ eul(p["head"])}
    for s_, (th, sh, ft) in LEGS.items():
        D[th] = Rr @ arc(RD["thigh" + s_], p["thigh" + s_])
        D[sh] = Rr @ arc(RD["shin" + s_], p["shin" + s_])
        D[ft] = D[sh] @ Rx(float(p["foot" + s_]))
    for s_, (a, f, h) in ARMS.items():
        D[a] = Dc @ arc(RD["arm" + s_], p["arm" + s_])
        D[f] = Dc @ arc(RD["fore" + s_], p["fore" + s_])
        D[h] = D[f]

    def run(hip):
        W, vals = [None] * NB, {}
        for i, v in enumerate(rest):
            pw = np.eye(4) if parent[i] < 0 else W[parent[i]]
            vv = v
            if i in D:
                local = np.linalg.inv(pw[:3, :3]) @ D[i] @ rest_W[i][:3, :3]
                t = v[:3].copy()
                if i == 2:
                    t = t + np.linalg.inv(pw[:3, :3]) @ hip
                e = euler_zyx(local)
                vals[i] = (*t, *e)
                vv = np.array([*t, *e, *v[6:9]])
            elif i == 1:
                t = v[:3] + np.array([0.0, 0.0, float(p["move"])])
                vals[1] = (*t, *v[3:6])
                vv = np.array([*t, *v[3:9]])
            W[i] = pw @ mat(vv)
        return W, vals

    pv = np.array(p["pivot"], dtype=float)
    hip = np.array(p["hip"], dtype=float) + pv - Rr @ pv
    W, vals = run(hip)
    g = float(p["ground"])
    if g > 0:
        low = min(W[b][1, 3] - rest_W[b][1, 3] for b in (10, 11, 16, 17))
        W, vals = run(hip + np.array([0.0, -low * g, 0.0]))
    return W, vals


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


class Anim:
    def __init__(self, actions, T, keys, keep_root=False, keep=(), shield_y=None, prop=None):
        self.actions = [actions] if isinstance(actions, str) else list(actions)
        self.T, self.keys, self.keep_root = T, sorted(keys, key=lambda k: k[0]), keep_root
        self.keep = tuple(keep) + ((1,) if keep_root else ())      # bones whose original tracks stay (same frame count needed)
        self.poses = sample(self.keys, T)
        self.solved = [solve(p) for p in self.poses]
        if prop is not None:            # bone 62 (child of the root, otherwise unused in these moves) carries the Chaos Emerald
            for f_, (W, vals) in enumerate(self.solved):
                r_ = prop(f_, W)
                pos, yaw, pitch = r_[0], r_[1], (r_[2] if len(r_) > 2 else 0.0)
                vals[62] = (float(pos[0]), float(pos[1]), float(pos[2]), math.radians(pitch), math.radians(yaw), 0.0)
        if shield_y is not None:        # put the shield bubble bone (61) at a fixed height above the floor
            for W, vals in self.solved:
                local = np.linalg.inv(W[parent[61]]) @ np.array([W[2][0, 3], shield_y, W[2][2, 3] + 0.3, 1.0])
                vals[61] = (*local[:3], *rest[61][3:6])


def write_anims(anims, aj_in, pl_in, aj_out, pl_out):
    aj = FighterAJManager(File.ReadAllBytes(aj_in))
    syms = list(aj.GetAnimationSymbols())
    order = sorted(syms, key=lambda s: aj.GetOffsetSize(s).Item1)
    tmp = tempfile.mkdtemp(prefix="sa_")
    for an in anims:
        frames = [v for _, v in an.solved]
        for action in an.actions:
            sym = [s for s in syms if s.endswith(f"ACTION_{action}_figatree")]
            if len(sym) != 1:
                raise SystemExit(f"animation for {action} not found exactly once")
            sym = sym[0]
            f = HSDRawFile(aj.GetAnimationData(sym))
            ft = f.Roots[0].Data
            nodes = ft.Nodes
            if an.keep and int(ft.FrameCount) != an.T:
                raise SystemExit(f"{action}: keep_root needs {int(ft.FrameCount)} frames, got {an.T}")
            for bi in range(nodes.Count):
                node = nodes[bi]
                if bi in an.keep:
                    continue
                node.Tracks.Clear()
                if bi not in frames[0]:
                    continue
                chans = list(zip(*[fr[bi] for fr in frames]))
                for ci, tt in enumerate(TT):
                    if ci < 3 and bi not in (1, 2, 61, 62):
                        continue
                    if bi == 1 and ci != 2:
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
            ft.FrameCount = float(an.T)
            p = os.path.join(tmp, f"{action}.dat")
            f.Save(p)
            aj.SetAnimation(sym, File.ReadAllBytes(p))
    new_aj = bytes(aj.RebuildAJFile(order, False))
    open(aj_out, "wb").write(new_aj)
    pos = {s: (aj.GetOffsetSize(s).Item1, aj.GetOffsetSize(s).Item2) for s in order}
    for s_, (o, z) in pos.items():
        if o < 0 or new_aj[o:o + z] != bytes(aj.GetAnimationData(s_)):
            raise SystemExit(f"offset check failed for {s_}")
    raw = bytearray(open(pl_in, "rb").read())
    base, acts = action_table(raw, pl_in)
    for k, a in enumerate(acts):
        name = a.SymbolName.Value if a.SymbolName is not None else None
        if name in pos:
            raw[base + k * 0x18 + 4: base + k * 0x18 + 12] = struct.pack(">ii", *pos[name])
    open(pl_out, "wb").write(raw)
    chk = list(HSDRawFile(pl_out).Roots[0].Data.FighterActionTable.Commands)
    bad = sum(1 for a in chk if a.SymbolName is not None and a.SymbolName.Value in pos and (a.AnimationOffset, a.AnimationSize) != pos[a.SymbolName.Value])
    print(f"animations written: {sum(len(a.actions) for a in anims)}; AJ {os.path.getsize(aj_in)} -> {len(new_aj)} bytes; re-read errors {bad}")
    if bad:
        raise SystemExit("offset patch failed")


def action_table(raw, pl_path):
    acts = list(HSDRawFile(pl_path).Roots[0].Data.FighterActionTable.Commands)
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
    return hits[0], acts


# ---------------------------------------------------------------- scripts
BYNAME = {d["name"]: d for d in sa.DEFS.values()}


def cmd(name, **kw):
    d = BYNAME[name]
    params = d.get("parameters") or []
    bits = 6 + sum(p["bitCount"] for p in params)
    n = max(4, (bits + 31) // 32 * 4)
    raw = d["code"] << (n * 8 - 6)
    pos = 6
    for p in params:
        v = kw.pop(p["name"], 0)
        if v < 0:
            v += 1 << p["bitCount"]
        raw |= v << (n * 8 - pos - p["bitCount"])
        pos += p["bitCount"]
    if kw:
        raise KeyError(f"{name}: unknown parameters {list(kw)}")
    return raw.to_bytes(n, "big")


def wait(n):
    return cmd("Synchronous Timer", Frame=n)


def at(f):
    return cmd("Asynchronous Timer", Frame=f)


CLEAR = cmd("Clear Hitboxes")
IASA = cmd("Allow Interrupt")
END = cmd("End Of Script")


def flag(v):
    return cmd("Set Flag", Flag=0, Value=v)


RANGE = 1.12   # v35: every hitbox 12% larger (user: slightly better range)


class Hit:
    """One hitbox. Offsets/size in units; x = along the bone (for bone 0: x side, y up, z forward)."""
    templates = {}

    def __init__(self, id, bone, dmg, size, angle, bkb, kbg, off=(0, 0, 0), wdsk=0, elem=0, tpl="kick"):
        self.__dict__.update(id=id, bone=bone, dmg=dmg, size=size, angle=angle, bkb=bkb, kbg=kbg, off=off, wdsk=wdsk, elem=elem, tpl=tpl)

    def bytes(self):
        data = bytearray(Hit.templates[self.tpl])
        c = sa.parse(bytes(data))[0]
        for k, v in (("ID", self.id), ("Bone", self.bone), ("Damage", self.dmg), ("Size", int(round(self.size * RANGE * 256))),
                     ("Z-Offset", int(round(self.off[0] * 256))), ("Y-Offset", int(round(self.off[1] * 256))), ("X-Offset", int(round(self.off[2] * 256))),
                     ("Angle", self.angle), ("Knockback Growth", self.kbg), ("Weight Set Knockback", self.wdsk),
                     ("Base Knockback", self.bkb), ("Element", self.elem)):
            sa.set_param(data, c, k, v)
        return bytes(data)


def load_templates(pl_path):
    for a in sa.load(pl_path):
        for key, name in (("kick", "AttackS3S"), ("punch", "Attack11")):
            if a.name == name:
                c = [c for c in a.cmds if c["name"] == "Create Hitbox"][0]
                Hit.templates[key] = a.data[c["off"]:c["off"] + c["len"]]


def build_script(parts):
    out = b""
    for p in parts:
        out += p.bytes() if isinstance(p, Hit) else p
    return out + END


def install_scripts(pl_in, pl_out, scripts, pointers=None):
    """scripts: {action name: bytes}. Appends each script to the data section and repoints the action table.
    pointers: {action name: [(offset in that script, data offset it must point at)]} for scripts that keep a Go To; each one is
    written into the script and added to the relocation table."""
    pointers = pointers or {}
    raw = bytearray(open(pl_in, "rb").read())
    base, acts = action_table(raw, pl_in)
    fsize, dsize, nrel, nroot, nref = struct.unpack(">5I", raw[:20])
    data = bytearray(raw[0x20:0x20 + dsize])
    tail = bytes(raw[0x20 + dsize:])
    names = {}
    for k, a in enumerate(acts):
        if a.SymbolName is not None:
            names.setdefault(a.SymbolName.Value.split("ACTION_")[1].replace("_figatree", ""), []).append(k)
    done, new_rel = {}, []
    for name, blob in scripts.items():
        if name not in names:
            raise SystemExit(f"no action named {name}")
        if blob not in done:
            while len(data) % 4:
                data += b"\0"
            done[blob] = len(data)
            data += blob
            for off, target in pointers.get(name, []):
                at_ = done[blob] + off
                data[at_:at_ + 4] = struct.pack(">I", target)
                new_rel.append(at_)
        for k in names[name]:
            ent = base - 0x20 + k * 0x18 + 0x0C
            old = struct.unpack(">I", data[ent:ent + 4])[0]
            if old == 0:
                raise SystemExit(f"{name}: action has no script pointer to replace")
            data[ent:ent + 4] = struct.pack(">I", done[blob])
    while len(data) % 4:
        data += b"\0"
    tail = tail[:4 * nrel] + struct.pack(f">{len(new_rel)}I", *new_rel) + tail[4 * nrel:]      # extra relocation entries
    nrel += len(new_rel)
    out = struct.pack(">5I", 0x20 + len(data) + len(tail), len(data), nrel, nroot, nref) + bytes(raw[20:0x20]) + bytes(data) + tail
    open(pl_out, "wb").write(out)
    after = {a.name: a for a in sa.load(pl_out) if a.name}
    for name, blob in scripts.items():
        if name in pointers:
            continue            # HSDRaw hands pointer fields back as zero, so these are checked by structure only
        if after[name].data[:len(blob)] != blob:
            raise SystemExit(f"{name}: script did not read back")
    print(f"scripts installed: {len(scripts)} actions, {len(done)} new scripts; PlSn.dat {len(raw)} -> {len(out)} bytes")


# ---------------------------------------------------------------- preview
COL = {"btest1": "#2346c8", "hara": "#e8c090", "eye2": "#ffffff", "hanasaki": "#111111", "hada": "#eec08c", "hoho": "#eec08c",
       "eye00": "#e8f4e8", "anakage": "#222222", "hando2": "#ffffff", "testhand": "#f4f4f4", "dwhite": "#ffffff",
       "shoose4": "#d02020", "shoose6": "#e04040", "kutusoko": "#888888", "kanagu": "#d8b020"}


def sheet(items, path, yaw=65, cols=7, hits=None):
    """items: [(label, Anim, [frames])]. Draws flat-shaded model poses, viewed from Sonic's front-left."""
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    from matplotlib.collections import PolyCollection
    from matplotlib.patches import Circle
    V = Ry(-yaw)   # view: screen x = (V @ p).x, depth = (V @ p).z
    tris = []
    for g in bd["groups"]:
        col = next((c for k, c in COL.items() if k in g["image"]), "#999999")
        c = g["c"]
        for n in range(0, len(c) - 2, 3):
            tris.append((col, [(c[n + j][0], np.array([*c[n + j][1:4], 1.0])) for j in range(3)]))
    fig, axs = plt.subplots(len(items), cols, figsize=(cols * 1.7, len(items) * 1.87), squeeze=False)
    for r, (label, an, frames) in enumerate(items):
        for cidx in range(cols):
            ax = axs[r][cidx]
            ax.set_xlim(-10, 10); ax.set_ylim(-2, 20); ax.set_aspect("equal"); ax.axis("off")
            if cidx >= len(frames):
                continue
            fr = frames[cidx]
            W = an.solved[fr][0]
            sh = np.eye(4); sh[2, 3] = -W[1][2, 3]
            W = [sh @ w for w in W]
            polys, cols_, depth = [], [], []
            for col, tri in tris:
                pts = [V @ (W[b] @ p)[:3] for b, p in tri]
                polys.append([(q[0], q[1]) for q in pts]); cols_.append(col); depth.append(sum(q[2] for q in pts))
            idx = np.argsort(depth)
            ax.add_collection(PolyCollection([polys[i] for i in idx], facecolors=[cols_[i] for i in idx], edgecolors="none"))
            ax.plot([-11, 11], [0, 0], color="#444444", lw=0.6)
            for (f0, f1, h) in (hits or {}).get(label, []):
                if f0 - 1 <= fr <= f1 - 1:
                    c3 = V @ (W[h.bone] @ np.array([*h.off, 1.0]))[:3]
                    ax.add_patch(Circle((c3[0], c3[1]), h.size, fill=False, color="red" if h.angle != 270 else "magenta", lw=0.8))
            ax.set_title(f"{label} {fr}" if cidx == 0 else str(fr), fontsize=6, pad=1)
    plt.subplots_adjust(left=0, right=1, top=0.97, bottom=0, wspace=0, hspace=0.12)
    fig.savefig(path, dpi=80)
    plt.close(fig)
    print("sheet", path)


def orig_bone_pos(aj_path, action, frame, bones):
    """World positions of bones in an existing animation of the AJ file (for matching ledge/hand positions)."""
    from HSDRaw.Tools import FOBJ_Player
    aj = FighterAJManager(File.ReadAllBytes(aj_path))
    sym = [s_ for s_ in aj.GetAnimationSymbols() if s_.endswith(f"ACTION_{action}_figatree")][0]
    ft = HSDRawFile(aj.GetAnimationData(sym)).Roots[0].Data
    CH = {"HSD_A_J_TRAX": 0, "HSD_A_J_TRAY": 1, "HSD_A_J_TRAZ": 2, "HSD_A_J_ROTX": 3, "HSD_A_J_ROTY": 4, "HSD_A_J_ROTZ": 5}
    W = []
    for i, v in enumerate(rest):
        v = v.copy()
        if i < ft.Nodes.Count:
            for t in ft.Nodes[i].Tracks:
                nm = str(t.JointTrackType)
                if nm in CH:
                    v[CH[nm]] = FOBJ_Player(t.ToFOBJ()).GetValue(float(frame))
        W.append(mat(v) if parent[i] < 0 else W[parent[i]] @ mat(v))
    return [W[b][:3, 3].copy() for b in bones]


def reach(pose, side, target, pole=(0.0, 0.0, 0.0)):
    """Two-bone IK: aim the `side` ("L"/"R") arm so its hand bone lands on `target` (fighter space, before grounding).
    `pole` is a world direction the elbow bends toward. Returns a new pose with arm/fore directions set (chest frame)."""
    a, f, h = ARMS[side]
    W, _ = solve(dict(pose, ground=0))
    S_, E_, H_ = W[a][:3, 3], W[f][:3, 3], W[h][:3, 3]
    L1, L2 = np.linalg.norm(rest_W[f][:3, 3] - rest_W[a][:3, 3]), np.linalg.norm(rest_W[h][:3, 3] - rest_W[f][:3, 3])
    T = np.array(target, dtype=float)
    d = T - S_
    dist = min(np.linalg.norm(d), (L1 + L2) * 0.999)
    dn = d / (np.linalg.norm(d) + 1e-9)
    cos_a = (L1 * L1 + dist * dist - L2 * L2) / (2 * L1 * dist)
    ang = math.acos(max(-1.0, min(1.0, cos_a)))
    pv = np.array(pole, dtype=float)
    pv = pv - dn * (pv @ dn)
    if np.linalg.norm(pv) < 1e-6:
        pv = np.cross(dn, [0.0, 1.0, 0.0]) if abs(dn[1]) < 0.9 else np.cross(dn, [1.0, 0.0, 0.0])
    pv = pv / np.linalg.norm(pv)
    elbow = S_ + L1 * (dn * math.cos(ang) + pv * math.sin(ang))
    hand = S_ + dn * dist
    Dc = eul(pose["root"]) @ eul(pose["chest"])
    out = dict(pose)
    out["arm" + side] = tuple(Dc.T @ unit(elbow - S_))
    out["fore" + side] = tuple(Dc.T @ unit(hand - elbow))
    return out


def head_point(pose, direction, out=0.5):
    """Surface point of Sonic's head (bone 39 geometry) furthest along `direction` (fighter space), pushed `out` beyond it."""
    W, _ = solve(dict(pose, ground=0))
    pts = np.array([(W[c[0]] @ np.array([*c[1:4], 1.0]))[:3] for g in bd["groups"] for c in g["c"] if c[0] == 39])
    dn = unit(direction)
    p = pts[np.argmax(pts @ dn)]
    return p + dn * out
