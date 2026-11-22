"""Measure ground moves on a standing Fox: first hit frame, damage per hit, and whether the move connects.

Usage: python move_test.py "<iso>" <P1: SONIC or libmelee name> <output prefix>
For each move: walk up to Fox, wait, do the move, log every frame, then back off and reset spacing.
The hit frame is P1's action frame on the frame P2's percent first rises (hitlag starts that frame).
"""
import csv
import sys
import time

from melee import enums

import harness
import runner

B = enums.Button
MAIN, CST = B.BUTTON_MAIN, B.BUTTON_C

# name -> function(controller, k) giving inputs on the k-th frame of the move (k from 0)
def jab(c, k):
    if k < 2: c.press_button(B.BUTTON_A)
def jab3(c, k):
    if k in (0, 1, 10, 11, 20, 21): c.press_button(B.BUTTON_A)
def ftilt(c, k):
    if k < 3: c.tilt_analog(MAIN, .78, .5)
    if 1 <= k < 3: c.press_button(B.BUTTON_A)
def utilt(c, k):
    if k < 3: c.tilt_analog(MAIN, .5, .78)
    if 1 <= k < 3: c.press_button(B.BUTTON_A)
def dtilt(c, k):
    if k < 12: c.tilt_analog(MAIN, .5, .2)
    if 9 <= k < 11: c.press_button(B.BUTTON_A)
def fsmash(c, k):
    if k < 2: c.tilt_analog(CST, 1, .5)
def usmash(c, k):
    if k < 2: c.tilt_analog(CST, .5, 1)
def dsmash(c, k):
    if k < 2: c.tilt_analog(CST, .5, 0)
def grab(c, k):
    if k < 2: c.press_button(B.BUTTON_Z)

def dash(c, k):
    if k < 14: c.tilt_analog(MAIN, 1, .5)
    if 12 <= k < 14: c.press_button(B.BUTTON_A)
def air(x, y, d=6, hold=2):
    def f(c, k):
        if k < hold: c.press_button(B.BUTTON_X)
        if d <= k < d + 2:
            if x is None: c.press_button(B.BUTTON_A)
            else: c.tilt_analog(CST, x, y)
    return f

# characters push each other apart at ~6.7 units, so nothing closer than ~7 is reachable by walking
MOVES = [("jab1", jab, 7.2), ("jab combo", jab3, 7.2), ("ftilt", ftilt, 8.0), ("utilt", utilt, 7.2), ("dtilt", dtilt, 8.0),
         ("fsmash", fsmash, 8.0), ("usmash", usmash, 7.2), ("dsmash", dsmash, 7.2), ("grab", grab, 7.2),
         ("dash attack", dash, 30.0), ("nair", air(None, None), 7.2), ("fair", air(1, .5), 7.2), ("bair", air(0, .5), 7.2), ("uair", air(.5, 1), 7.2), ("dair", air(.5, 0), 7.2)]
def sp(x, y, hold=2, jump=None, at=0):
    def f(c, k):
        if jump is not None and k < 2: c.press_button(B.BUTTON_X)
        if at <= k < at + hold:
            c.press_button(B.BUTTON_B)
            if k < at + 3: c.tilt_analog(MAIN, x, y)
    return f
if "--specials" in sys.argv:
    def twice(c, k):
        if k < 2 or 30 <= k < 32: c.press_button(B.BUTTON_B)
    MOVES = [("homing miss x2", twice, 82.0), ("homing 40", sp(.5, .5), 40.0),
             ("spin dash tap", sp(1, .5, hold=3), 40.0), ("spin dash charged", sp(1, .5, hold=40), 60.0),
             ("light speed dash", sp(.5, 1), 20.0), ("lsd diagonal", sp(.85, .85), 20.0),
             ("bounce ground", sp(.5, 0), 7.5), ("bounce air", sp(.5, 0, jump=1, at=16), 7.5)]
if "--air" in sys.argv:
    def bair2(d):
        def f(c, k):
            if k < 2: c.tilt_analog(MAIN, .3, .5)
            if 14 <= k < 16: c.press_button(B.BUTTON_X)
            if 14 + d <= k < 16 + d: c.tilt_analog(CST, 1, .5)
        return f
    MOVES = [(f"bair d{d}", bair2(d), 7.2) for d in (24, 28, 32, 36)] + [(f"dair d{d}", air(.5, 0, d), 7.2) for d in (20, 26)] + [(f"nair d{d}", air(None, None, d), 7.2) for d in (24,)]
    FAIR_ONLY = list(MOVES)
    def bair(d):
        def f(c, k):
            if k < 2: c.tilt_analog(MAIN, .3, .5)          # turn away from Fox
            if 14 <= k < 16: c.press_button(B.BUTTON_X)
            if 14 + d <= k < 16 + d: c.tilt_analog(CST, 1, .5)
        return f
    MOVES += [(f"bair d{d}", bair(d), 7.2) for d in (6, 12, 18)]
    MOVES += [(f"uair d{d}", air(.5, 1, d), 7.2) for d in (5, 20, 28)]
    MOVES += [("uair fulljump d8", air(.5, 1, 8, 12), 7.2), ("dair d6", air(.5, 0, 6), 7.2), ("dair d14", air(.5, 0, 14), 7.2)]
if "--fair" in sys.argv: MOVES = FAIR_ONLY
FOX_HOME = 15.0
SHOTS = {"jab combo": 27, "ftilt": 10, "fsmash": 16, "usmash": 14, "dsmash": 9, "dash attack": 20, "nair": 16, "fair": 21, "dair": 16} if "--shots" in sys.argv else {}
if "--faceshot" in sys.argv:
    def turn(c, k):
        if k < 2: c.tilt_analog(MAIN, .25, .5)
    def shield(c, k):
        if k < 50: c.press_button(B.BUTTON_R)
    def gthrow(x, y):
        def f(c, k):
            if k < 2: c.press_button(B.BUTTON_Z)
            if 34 <= k < 37: c.tilt_analog(MAIN, x, y)
        return f
    def crouch(c, k):
        if k < 40: c.tilt_analog(MAIN, .5, 0)
    def taunt(c, k):
        if k < 2: c.press_button(B.BUTTON_D_UP)
    def upb_side(c, k):
        if k < 2:
            c.press_button(B.BUTTON_B); c.tilt_analog(MAIN, .5, 1)
        elif k < 14: c.tilt_analog(MAIN, 1, .5)
    def downb_jump(c, k):
        if k < 132:
            c.press_button(B.BUTTON_B)
            if k < 3: c.tilt_analog(MAIN, .5, 0)
        if 124 <= k < 127: c.press_button(B.BUTTON_X)
    def downb_early(c, k):
        if k < 60:
            c.press_button(B.BUTTON_B)
            if k < 3: c.tilt_analog(MAIN, .5, 0)
        if 40 <= k < 43: c.press_button(B.BUTTON_X)
    def runr(c, k):
        if k < 45: c.tilt_analog(MAIN, 1, .5)
    def crouch2(c, k):
        if k < 50: c.tilt_analog(MAIN, .5, 0)
    MOVES = [("crouch", crouch2, 14.0, 60), ("fsmash face", fsmash, 9.0, 60), ("ftilt 16", ftilt, 16.0), ("dtilt 8", dtilt, 8.0), ("dtilt 12", dtilt, 12.0),
             ("fsmash 24", fsmash, 24.0), ("homing 40", sp(.5, .5), 40.0), ("homing miss", sp(.5, .5), 82.0),
             ("down b jump", downb_jump, 60.0, 190), ("down b early jump", downb_early, 60.0), ("up b", sp(.5, 1), 20.0), ("up b side", upb_side, 60.0)]
    SHOTS = {"crouch": (30,), "fsmash face": (16,), "dtilt 12": (15, 20), "up b": (5, 14), "up b side": (14,)}
if "--spinshots" in sys.argv:
    MOVES = [("spin dash charged", sp(1, .5, hold=40), 60.0), ("nair", air(None, None), 20.0), ("homing 40", sp(.5, .5), 40.0)]
    SHOTS = {"spin dash charged": (4, 14, 30, 46, 52, 90), "nair": (5, 12, 18, 40), "homing 40": (6, 30)}


def main():
    iso, p1, prefix = sys.argv[1], sys.argv[2], sys.argv[3]
    harness.DISABLE_CODES = ["$Required: Slippi Online"]
    harness.OFFSCREEN = True
    if "--big" in sys.argv: harness.WIN = (1280, 1000)
    r = runner.Runner(iso, prefix)
    target = (harness.SONIC_CSS_X, harness.SONIC_CSS_Y) if p1 == "SONIC" else runner.vanilla_css_pos(enums.Character[p1])
    rows, results = [], []
    try:
        r.start()
        if not r.go_to_match(target, runner.vanilla_css_pos(enums.Character.FOX)):
            print("RESULT: FAIL (menus)"); return
        c = r.s.c1
        mi, phase, k, frames, cur = 0, "approach", 0, 0, None
        t0 = time.time()
        while time.time() - t0 < 560 and mi < len(MOVES):
            gs = r.s.console.step()
            if gs is None:
                time.sleep(0.001); continue
            if gs.menu_state not in (enums.Menu.IN_GAME, enums.Menu.SUDDEN_DEATH):
                continue
            frames += 1
            a, b = gs.players[1], gs.players[2]
            act = a.action.name if hasattr(a.action, "name") else str(a.action)
            bact = b.action.name if hasattr(b.action, "name") else str(b.action)
            name, fn, dist = MOVES[mi][:3]
            dur = MOVES[mi][3] if len(MOVES[mi]) > 3 else 110
            dx = float(b.position.x - a.position.x)
            rows.append([frames, name, phase, k, act, a.action_frame, round(float(a.position.x), 2), round(dx, 2), b.percent, bact])
            c.release_all()
            c2 = r.s.c2
            c2.release_all()
            fox_x = float(b.position.x)
            fox_home = phase in ("approach", "reset") and abs(fox_x - FOX_HOME) > 3 and bact in ("STANDING", "WALK_SLOW", "WALK_MIDDLE", "WALK_FAST", "TURNING") and abs(float(b.position.y)) < 0.1
            if frames >= 130 and fox_home:
                c2.tilt_analog(MAIN, .7 if fox_x < FOX_HOME else .3, .5)   # walk Fox back to the middle
            if frames < 130:
                pass
            elif phase == "approach":
                # Fox must be standing still on the ground near the middle; walk slowly to the test distance
                if bact != "STANDING" or abs(float(b.position.y)) > 0.1 or fox_home:
                    if dx < 9:
                        c.tilt_analog(MAIN, .32, .5)      # give Fox room to walk home
                elif dx > dist + 0.8:
                    c.tilt_analog(MAIN, .68, .5)
                elif dx < dist - 0.8 and not (dist < 0 and not a.facing):
                    c.tilt_analog(MAIN, .32, .5)
                elif act == "STANDING" and a.facing:
                    phase, k = "settle", 0
                elif not a.facing:
                    c.tilt_analog(MAIN, .85, .5)      # turn around to face Fox
            elif phase == "settle":
                k += 1
                if k >= 20:
                    phase, k = "move", 0
                    cur = {"move": name, "dist": round(dx, 2), "pct0": b.percent, "hits": [], "actions": []}
            elif phase == "move":
                fn(c, k)
                if k in SHOTS.get(name, ()) if isinstance(SHOTS.get(name), tuple) else SHOTS.get(name) == k:
                    print("capture", name, r.s.capture_game(f"{prefix}_{name.replace(' ', '_')}_{k}.png"), flush=True)
                px, py = float(a.position.x), float(a.position.y)
                cur.setdefault("x0", px)
                cur["xmax"], cur["ymax"], cur["ymin"] = max(cur.get("xmax", px), px), max(cur.get("ymax", py), py), min(cur.get("ymin", py), py)
                if act not in cur["actions"]:
                    cur["actions"].append(act)
                last = cur["hits"][-1][2] if cur["hits"] else cur["pct0"]
                if b.percent > last:
                    cur["hits"].append((act, a.action_frame, b.percent, round(b.percent - last, 1)))
                    cur["kbwait"] = True
                kx, ky = float(getattr(b, "speed_x_attack", 0) or 0), float(getattr(b, "speed_y_attack", 0) or 0)
                if cur.get("kbwait") and (abs(kx) > 0.01 or abs(ky) > 0.01):
                    cur.setdefault("kb", []).append((round(kx, 2), round(ky, 2), round(float(a.position.y), 1)))
                    cur["kbwait"] = False
                if "GRAB" in bact.upper() or "CAPTURE" in bact.upper() or bact.startswith("GRABBED"):
                    cur["grabbed"] = cur.get("grabbed") or (act, a.action_frame, bact)
                k += 1
                if k >= dur:
                    results.append(cur)
                    phase, k = "reset", 0
                    mi += 1
            elif phase == "reset":
                k += 1
                if k >= 90:
                    phase, k = "approach", 0
            c.flush(); c2.flush()
    finally:
        r.stop()
    with open(prefix + "_frames.csv", "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["frame", "move", "phase", "k", "p1_action", "p1_action_frame", "p1_x", "dx", "p2_pct", "p2_action"])
        w.writerows(rows)
    for res in results:
        hits = "; ".join(f"{h[0]} f{h[1]} +{h[3]}%" for h in res["hits"]) or "NO HIT"
        hits += f" | kb {res['kb']}" if res.get("kb") else ""
        hits += f" | moved x {res.get('xmax', 0) - res.get('x0', 0):+.1f}, y {res.get('ymin', 0):.1f}..{res.get('ymax', 0):.1f}"
        extra = f" | grabbed during {res['grabbed'][0]} f{res['grabbed'][1]} ({res['grabbed'][2]})" if res.get("grabbed") else ""
        print(f"MOVE {res['move']:10} dist {res['dist']:5} | {hits}{extra} | actions {res['actions'][:8]}", flush=True)
    print("RESULT:", "OK" if len(results) == len(MOVES) else f"INCOMPLETE ({len(results)}/{len(MOVES)})", flush=True)


if __name__ == "__main__":
    main()
