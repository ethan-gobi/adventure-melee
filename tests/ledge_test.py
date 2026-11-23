"""Ledge options on Final Destination: P1 grabs the right ledge, then climbs, attacks, rolls and jumps from it.

Usage: python ledge_test.py "<iso>" <P1: SONIC or libmelee name> <output prefix> [--big]
Each trial: walk to the right edge, turn to face the stage, jump backwards off it, drift back and grab the ledge,
hang 30 frames, do the option. Logs the action sequence and P1's position; captures frames listed in SHOTS.
"""
import sys
import time

from melee import enums

import harness
import runner

B = enums.Button
MAIN = B.BUTTON_MAIN
EDGE = 85.5657            # Final Destination's right ledge


def press(btn):
    def f(c, k):
        if k < 3:
            c.press_button(btn)
    return f


def climb(c, k):
    if k < 3:
        c.tilt_analog(MAIN, 0.5, 1.0)      # up = climb (a tap toward the stage did nothing in the v60 run)


OPTIONS = [("climb", climb, 70), ("attack", press(B.BUTTON_A), 80), ("roll", press(B.BUTTON_R), 80), ("jump", press(B.BUTTON_X), 70)]
SHOTS = {"hang": (12,), "climb": (4, 9, 15, 22, 30), "attack": (6, 14, 20, 25, 34), "roll": (6, 13, 20, 28, 40), "jump": (3, 8, 14, 22)}


def main():
    iso, p1, prefix = sys.argv[1], sys.argv[2], sys.argv[3]
    harness.DISABLE_CODES = ["$Required: Slippi Online"]
    harness.OFFSCREEN = True
    if "--big" in sys.argv:
        harness.WIN = (1280, 1000)
    r = runner.Runner(iso, prefix)
    target = (harness.SONIC_CSS_X, harness.SONIC_CSS_Y) if p1 == "SONIC" else runner.vanilla_css_pos(enums.Character[p1])
    done = []
    try:
        r.start()
        if not r.go_to_match(target, runner.vanilla_css_pos(enums.Character.FOX)):
            print("RESULT: FAIL (menus)"); return
        c, c2 = r.s.c1, r.s.c2
        oi, phase, k, frames, cur, hung, lastx = 0, "go", 0, 0, None, False, 0.0
        t0 = time.time()
        while time.time() - t0 < 240 and oi < len(OPTIONS):
            gs = r.s.console.step()
            if gs is None:
                time.sleep(0.001); continue
            if gs.menu_state not in (enums.Menu.IN_GAME, enums.Menu.SUDDEN_DEATH):
                continue
            frames += 1
            a = gs.players[1]
            act = a.action.name if hasattr(a.action, "name") else str(a.action)
            x, y = float(a.position.x), float(a.position.y)
            c.flush(); c2.flush()            # send last frame's inputs (unflushed inputs arrived late or not at all)
            c.release_all(); c2.release_all()
            px, lastx = lastx, x
            if frames < 120:
                pass
            elif phase == "go":                      # stand 6-12 units from the edge, facing the stage (left)
                if act in ("EDGE_HANGING", "EDGE_CATCHING"):
                    phase, k = "hang", 0
                elif abs(y) > 0.5 or act not in ("STANDING", "WALK_SLOW", "WALK_MIDDLE", "WALK_FAST", "TURNING", "DASHING", "RUNNING"):
                    if y < -5 and x > EDGE:
                        c.tilt_analog(MAIN, 0.0, 0.5)    # fell: drift back to the ledge
                elif x < EDGE - 12:
                    c.tilt_analog(MAIN, 0.72, 0.5)
                elif x > EDGE - 6:
                    c.tilt_analog(MAIN, 0.35, 0.5)
                elif a.facing:
                    c.tilt_analog(MAIN, 0.3, 0.5)        # turn round
                elif act == "STANDING":
                    phase, k = "jump", 0
            elif phase == "jump":                    # back jump off the edge, then drift back and fall onto the ledge
                if k % 8 == 0 and "--trace" in sys.argv:
                    print(f"  jump k{k} {act} x {x:.1f} y {y:.1f} facing_right {a.facing}", flush=True)
                if act in ("EDGE_HANGING", "EDGE_CATCHING"):
                    phase, k = "hang", 0
                elif k < 4:
                    c.press_button(B.BUTTON_X); c.tilt_analog(MAIN, 1.0, 0.5)
                else:                                # steer so he falls past the ledge about 5 units out, facing the stage
                    pred = x + (x - px) * 10
                    if pred < EDGE + 4.5:
                        c.tilt_analog(MAIN, 1.0, 0.5)
                    elif pred > EDGE + 5.5:
                        c.tilt_analog(MAIN, 0.0, 0.5)
                k += 1
                if k > 200:
                    print("could not grab the ledge; retrying"); phase, k = "go", 0
            elif phase == "hang":
                if not hung and k in SHOTS["hang"]:
                    print("capture hang", r.s.capture_game(f"{prefix}_hang_{k}.png"), flush=True)
                if k == 1:
                    print(f"hang at x {x:.2f} y {y:.2f} ({act})", flush=True)
                k += 1
                if k >= 30:
                    hung = True
                    phase, k = "opt", 0
                    cur = {"name": OPTIONS[oi][0], "actions": [], "start": (round(x, 1), round(y, 1))}
            elif phase == "opt":
                name, fn, dur = OPTIONS[oi]
                fn(c, k)
                if k in SHOTS.get(name, ()):
                    print("capture", name, r.s.capture_game(f"{prefix}_{name}_{k}.png"), flush=True)
                if not cur["actions"] or cur["actions"][-1][0] != act:
                    cur["actions"].append([act, k])
                k += 1
                if k >= dur:
                    cur["end"] = (round(x, 1), round(y, 1))
                    print(f"LEDGE {name:7} | start {cur['start']} end {cur['end']} | " + " ".join(f"{n}@{f}" for n, f in cur["actions"]), flush=True)
                    done.append(cur)
                    oi += 1
                    phase, k = "go", 0
        print(f"RESULT: {'OK' if len(done) == len(OPTIONS) else 'INCOMPLETE'} ({len(done)}/{len(OPTIONS)})")
    finally:
        r.stop()


if __name__ == "__main__":
    main()
