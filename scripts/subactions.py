"""Decode Melee fighter subaction scripts from a Pl??.dat using HSDRawViewer's command definitions.

Library use:  acts = load(pl_path)  -> list of Action(name, index, data(bytes), cmds, frame_count)
CLI:          python subactions.py <PlXx.dat> [<PlXxAJ.dat>] [name filter regex]   prints a move table
"""
import os
import re
import sys

import yaml

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from hsd import *  # noqa: E402,F401

YML = r"C:\adventure-melee\tools\HSDRaw\Scripts\command_fighter.yml"
DEFS = {d["code"]: d for y in (YML.replace("command_fighter", "command_controls"), YML) for d in yaml.safe_load(open(y, encoding="utf-8-sig"))}


def cmd_len(code):
    d = DEFS.get(code)
    bits = 6 + sum(p["bitCount"] for p in (d.get("parameters") or [])) if d else 32
    return max(4, (bits + 31) // 32 * 4)


def parse(data):
    """-> list of dicts {off, code, name, len, params{name: value}}; stops at the end command (code 0)."""
    out, off = [], 0
    while off + 4 <= len(data):
        code = data[off] >> 2
        n = cmd_len(code)
        raw = int.from_bytes(data[off:off + n], "big")
        total = n * 8
        pos = 6
        params = {}
        d = DEFS.get(code, {"name": f"cmd_{code}", "parameters": []})
        for p in d.get("parameters") or []:
            bc = p["bitCount"]
            v = (raw >> (total - pos - bc)) & ((1 << bc) - 1)
            if p.get("signed") and v >> (bc - 1):
                v -= 1 << bc
            params[p["name"]] = v
            pos += bc
        out.append({"off": off, "code": code, "name": d["name"], "len": n, "params": params})
        off += n
        if code == 0:
            break
    return out


def set_param(data, cmd, name, value):
    """Write one parameter of a parsed command back into a bytearray (same length, in place)."""
    d = DEFS[cmd["code"]]
    n, total, pos = cmd["len"], cmd["len"] * 8, 6
    raw = int.from_bytes(data[cmd["off"]:cmd["off"] + n], "big")
    for p in d["parameters"]:
        bc = p["bitCount"]
        if p["name"] == name:
            if value < 0:
                value += 1 << bc
            if not 0 <= value < (1 << bc):
                raise ValueError(f"{name}={value} does not fit in {bc} bits")
            shift = total - pos - bc
            raw = (raw & ~(((1 << bc) - 1) << shift)) | (value << shift)
            data[cmd["off"]:cmd["off"] + n] = raw.to_bytes(n, "big")
            cmd["params"][name] = value if not (p.get("signed") and value >> (bc - 1)) else value - (1 << bc)
            return
        pos += bc
    raise KeyError(name)


class Action:
    pass


def load(pl_path, aj_path=None):
    fd = HSDRawFile(pl_path).Roots[0].Data
    frames = {}
    if aj_path:
        from System.IO import File
        from HSDRaw.Tools.Melee import FighterAJManager
        aj = FighterAJManager(File.ReadAllBytes(aj_path))
        for s in aj.GetAnimationSymbols():
            frames[s] = HSDRawFile(aj.GetAnimationData(s)).Roots[0].Data.FrameCount
    acts = []
    for i, a in enumerate(fd.FighterActionTable.Commands):
        act = Action()
        act.index = i
        act.symbol = a.SymbolName.Value if a.SymbolName is not None else None
        m = re.search(r"ACTION_(.+)_figatree", act.symbol or "")
        act.name = m.group(1) if m else None
        act.data = bytes(a.SubAction._s.GetData()) if a.SubAction is not None else b""
        act.cmds = parse(act.data) if act.data else []
        act.frame_count = frames.get(act.symbol)
        acts.append(act)
    return acts


def timeline(act):
    """Walk the script: -> (hitbox events, iasa frame). Frames are 1-based like frame-data tables."""
    frame = 1
    active = {}
    events = []   # (start, end, params)
    iasa = None
    for c in act.cmds:
        p = c["params"]
        if c["name"] == "Synchronous Timer":
            frame += list(p.values())[0]
        elif c["name"] == "Asynchronous Timer":
            frame = list(p.values())[0]
        elif c["name"] == "Create Hitbox":
            if p["ID"] in active:
                events.append((active[p["ID"]][0], frame - 1, active[p["ID"]][1]))
            active[p["ID"]] = (frame, p)
        elif c["name"] == "Remove Hitbox":
            hid = list(p.values())[0]
            if hid in active:
                events.append((active[hid][0], frame - 1, active[hid][1]))
                del active[hid]
        elif c["name"] == "Clear Hitboxes":
            for hid, (st, hp) in active.items():
                events.append((st, frame - 1, hp))
            active = {}
        elif "interrupt" in c["name"].lower() or "IASA" in c["name"]:
            iasa = frame
    for hid, (st, hp) in active.items():
        events.append((st, act.frame_count or st, hp))
    return sorted(events, key=lambda e: (e[0], e[2]["ID"])), iasa


if __name__ == "__main__":
    pl = sys.argv[1]
    aj = sys.argv[2] if len(sys.argv) > 2 and sys.argv[2].lower().endswith(".dat") else None
    flt = re.compile(sys.argv[-1]) if len(sys.argv) > 2 and not sys.argv[-1].lower().endswith(".dat") else re.compile("Attack|Catch|Throw")
    for act in load(pl, aj):
        if not act.name or not flt.search(act.name):
            continue
        ev, iasa = timeline(act)
        print(f"{act.name}  (action {act.index}, total {act.frame_count}, IASA {iasa}, script {len(act.data)} bytes)")
        for st, en, p in ev:
            print(f"    hitbox {p['ID']} f{st}-{en}: dmg {p['Damage']} angle {p['Angle']} bkb {p.get('Base Knockback')} kbg {p['Knockback Growth']} wdsk {p['Weight Set Knockback']}"
                  f" size {p['Size']} bone {p['Bone']} off({p['X-Offset']},{p['Y-Offset']},{p['Z-Offset']}) elem {p.get('Element')}")
