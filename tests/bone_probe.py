"""Print where the game really puts some of P1's bones (world position and local translation) while he stands,
shields (R held) and spot dodges. Used to see what the engine does to the skeleton in shield states.

Usage: python bone_probe.py "<iso>" <P1: SONIC or libmelee name> <output prefix>
"""
import struct
import sys
import time

from melee import enums

import harness
import runner

B = enums.Button
MAIN = B.BUTTON_MAIN
BONES = (0, 1, 2, 3, 4, 19, 39, 61)


def bones(m):
    g = m.u32(0x80453080 + 0xB0)
    fd = m.u32(g + 0x2C)
    arr = m.u32(fd + 0x5E8)          # FighterBone array (0x10 each, joint pointer first)
    out = {}
    for b in BONES:
        j = m.u32(arr + b * 0x10)
        if not j or not (0x80000000 <= j < 0x81800000):
            out[b] = None
            continue
        raw = m.read(j + 0x38, 12)
        mt = m.read(j + 0x44, 48)
        loc = struct.unpack(">3f", raw)
        mtx = struct.unpack(">12f", mt)
        out[b] = (tuple(round(v, 2) for v in loc), (round(mtx[3], 2), round(mtx[7], 2), round(mtx[11], 2)))
    frame = struct.unpack(">f", m.read(fd + 0x894, 4))[0]
    state = m.u32(fd + 0x10)
    return state, round(frame, 2), out


def main():
    iso, p1, prefix = sys.argv[1], sys.argv[2], sys.argv[3]
    harness.DISABLE_CODES = ["$Required: Slippi Online"]
    harness.OFFSCREEN = True
    r = runner.Runner(iso, prefix)
    target = (harness.SONIC_CSS_X, harness.SONIC_CSS_Y) if p1 == "SONIC" else runner.vanilla_css_pos(enums.Character[p1])
    try:
        r.start()
        if not r.go_to_match(target, runner.vanilla_css_pos(enums.Character.FOX)):
            print("RESULT: FAIL (menus)"); return
        c = r.s.c1
        frames = 0
        t0 = time.time()
        while time.time() - t0 < 60 and frames < 420:
            gs = r.s.console.step()
            if gs is None:
                time.sleep(0.001); continue
            if gs.menu_state not in (enums.Menu.IN_GAME, enums.Menu.SUDDEN_DEATH):
                continue
            frames += 1
            k = frames - 150
            if k == 0:
                c.release_all()
            if k == 1:
                c.press_button(B.BUTTON_R)            # held (never released) until k = 90
            if k == 90:
                c.release_all()
            if k == 140:
                c.press_button(B.BUTTON_R)
            if k == 146:
                c.tilt_analog(MAIN, 0.5, 0.0)         # spot dodge
            if k == 152:
                c.release_all()
            c.flush()
            if k in (-5, 3, 6, 12, 30, 60, 88, 92, 96, 150, 156, 160, 200):
                st, fr, out = bones(r.m)
                a = gs.players[1]
                print(f"k{k:4} state {st} ({a.action.name}) anim frame {fr} pos y {float(a.position.y):.2f}", flush=True)
                for b, v in out.items():
                    print(f"       bone {b:2}: local T {v[0]}  world {v[1]}" if v else f"       bone {b}: -", flush=True)
        print("RESULT: OK")
    finally:
        r.stop()


if __name__ == "__main__":
    main()
