"""Being grabbed, knocked down and getting up, on Final Destination.

Usage: python knock_test.py "<iso>" <P1: SONIC or libmelee name> <output prefix> [--big]
P2 (Fox) first grabs P1 and pummels once (captures of the held and pummeled poses), then walks up and up-smashes him
again and again. P1 never techs: every time he ends up lying on the floor he waits (capture), then uses the next get-up
option (stand, attack, roll forward, roll back). Logs P1's action sequence for each one and captures the frames in SHOTS.
"""
import sys
import time

from melee import enums

import harness
import runner

B = enums.Button
MAIN, CSTICK = B.BUTTON_MAIN, B.BUTTON_C
OPTIONS = [("stand", lambda c: c.tilt_analog(MAIN, 0.5, 1.0)), ("attack", lambda c: c.press_button(B.BUTTON_A)),
           ("rollF", lambda c: c.tilt_analog(MAIN, 1.0, 0.5)), ("rollB", lambda c: c.tilt_analog(MAIN, 0.0, 0.5))]
SHOTS = (4, 10, 16, 20, 24, 28, 34)
LYING = ("LYING_GROUND_UP", "LYING_GROUND_DOWN")
HELD = ("GRAB_PULL", "GRABBED", "GRAB_PUMMELED", "GRAB_PULLING_HIGH", "GRABBED_WAIT_HIGH", "GRAB_NECK", "GRAB_FOOT")
NEUTRAL = ("STANDING", "WALK_SLOW", "WALK_MIDDLE", "WALK_FAST", "TURNING", "LANDING", "CROUCH_END")


def main():
    iso, p1, prefix = sys.argv[1], sys.argv[2], sys.argv[3]
    want = int(sys.argv[sys.argv.index("--count") + 1]) if "--count" in sys.argv else 8
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
        frames, phase, k, oi, cool, grabs, last, seq = 0, "grab", 0, 0, 0, 0, None, []
        cur = None
        t0 = time.time()
        while time.time() - t0 < 300 and len(done) < want:
            gs = r.s.console.step()
            if gs is None:
                time.sleep(0.001); continue
            if gs.menu_state not in (enums.Menu.IN_GAME, enums.Menu.SUDDEN_DEATH):
                continue
            frames += 1
            a, f = gs.players[1], gs.players[2]
            act = a.action.name if hasattr(a.action, "name") else str(a.action)
            fact = f.action.name if hasattr(f.action, "name") else str(f.action)
            x, y, fx = float(a.position.x), float(a.position.y), float(f.position.x)
            c.flush(); c2.flush()            # send last frame's inputs (unflushed inputs arrived late or not at all)
            c.release_all(); c2.release_all()
            if act != last:
                seq.append(f"{act}@{frames}")
                last = act
            if frames < 120:
                continue
            cool = max(0, cool - 1)
            # ---- P1: lie there, then one get-up option
            if act in LYING:
                if phase != "lying":
                    phase, k = "lying", 0
                    cur = {"lie": act, "name": OPTIONS[oi % len(OPTIONS)][0], "pct": int(a.percent), "actions": []}
                if k == 12:
                    print("capture lying", act, r.s.capture_game(f"{prefix}_lie{len(done)}_{act[-2:]}.png"), flush=True)
                if 18 <= k < 21:
                    OPTIONS[oi % len(OPTIONS)][1](c)
                k += 1
            elif phase == "lying":
                cur["lay"] = k
                phase, k = "getup", 0
            if phase == "getup":
                if not cur["actions"] or cur["actions"][-1][0] != act:
                    cur["actions"].append([act, k])
                if k in SHOTS:
                    print("capture", cur["name"], r.s.capture_game(f"{prefix}_{len(done)}{cur['name']}_{k}.png"), flush=True)
                k += 1
                if k > 62:
                    print(f"KNOCK {cur['name']:6} from {cur['lie']:18} at {cur['pct']}% after lying {cur['lay']} frames | end x {x:.1f} y {y:.1f} | "
                          + " ".join(f"{n}@{fr}" for n, fr in cur["actions"]), flush=True)
                    done.append(cur)
                    oi += 1
                    phase, k = "knock", 0
            if act.startswith("TECH_MISS"):
                if phase != "bound":
                    phase, k = "bound", 0
                if k in (2, 9, 16):
                    print("capture bound", act, r.s.capture_game(f"{prefix}_bound{len(done)}_{k}.png"), flush=True)
                k += 1
            # ---- held by Fox
            if act in HELD:
                if phase != "held":
                    phase, k = "held", 0
                    grabs += 1
                if k in (3, 14, 30, 44):
                    print("capture held", act, r.s.capture_game(f"{prefix}_held{grabs}_{k}.png"), flush=True)
                if 34 <= k < 36:
                    c2.press_button(B.BUTTON_A)        # one pummel
                k += 1
                continue
            if phase == "held":
                phase, k = ("grab", 0) if grabs < 1 else ("knock", 0)
                cool = 50
            # ---- P2: grab once, then up smash whenever P1 is standing
            if act in NEUTRAL and fact in NEUTRAL and abs(y) < 0.5 and cool == 0 and phase in ("grab", "knock"):
                d = x - fx
                if abs(d) > (6.5 if phase == "grab" else 5.0):
                    c2.tilt_analog(MAIN, 0.5 + (0.3 if d > 0 else -0.3), 0.5)
                elif (d > 0) != bool(f.facing) and phase == "grab":
                    c2.tilt_analog(MAIN, 0.5 + (0.25 if d > 0 else -0.25), 0.5)      # turn to face him
                elif phase == "grab":
                    c2.press_button(B.BUTTON_Z)
                    cool = 40
                else:
                    c2.tilt_analog(CSTICK, 0.5, 1.0)
                    cool = 55
        print("P1 action sequence:", " ".join(seq[-120:]))
        print(f"RESULT: {'OK' if len(done) >= want else 'INCOMPLETE'} ({len(done)}/{want} get-ups, {grabs} grabs)")
    finally:
        r.stop()


if __name__ == "__main__":
    main()
