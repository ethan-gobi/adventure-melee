"""Recovery checks on Final Destination's left edge (Fox stays far right, so Homing Attack has no target):
  cancel : jump, air up B (Tails), press R 20 frames in, then try up B again (should not start)
  ledge  : walk off the left edge, fall to y -25, air up B holding toward the stage: does he grab the ledge?
  homing : jump off the left edge, neutral B into empty air, then double jump + up B back toward the stage
Usage: python recovery_test.py "<iso>" <P1: SONIC or libmelee name> <output prefix>
"""
import sys
import time

from melee import enums

import harness
import runner

B = enums.Button
MAIN = B.BUTTON_MAIN
EDGE = -85.5657
TAILS = "SWORD_DANCE_2_MID"     # libmelee's name for state 351
SCEN = ["cancel", "ledge", "homing"]


def main():
    iso, p1, prefix = sys.argv[1], sys.argv[2], sys.argv[3]
    harness.DISABLE_CODES = ["$Required: Slippi Online"]
    harness.OFFSCREEN = True
    harness.WIN = (1280, 1000)
    r = runner.Runner(iso, prefix)
    target = (harness.SONIC_CSS_X, harness.SONIC_CSS_Y) if p1 == "SONIC" else runner.vanilla_css_pos(enums.Character[p1])
    try:
        r.start()
        if not r.go_to_match(target, runner.vanilla_css_pos(enums.Character.FOX)):
            print("RESULT: FAIL (menus)"); return
        c = r.s.c1
        frames, si, phase, k, seq, last, stocks = 0, 0, "setup", 0, [], None, None
        t0 = time.time()
        while time.time() - t0 < 200 and si < len(SCEN):
            gs = r.s.console.step()
            if gs is None:
                time.sleep(0.001); continue
            if gs.menu_state not in (enums.Menu.IN_GAME, enums.Menu.SUDDEN_DEATH):
                continue
            frames += 1
            a = gs.players[1]
            act = a.action.name if hasattr(a.action, "name") else str(a.action)
            x, y = float(a.position.x), float(a.position.y)
            stocks = a.stock if stocks is None else stocks
            c.release_all()
            name = SCEN[si]
            if frames < 140:
                c.flush(); continue
            if phase == "setup":          # stand on stage, near the left edge (cancel: anywhere)
                want = -60.0 if name == "cancel" else EDGE + 9
                if act not in ("STANDING", "WALK_SLOW", "WALK_MIDDLE", "WALK_FAST", "TURNING", "DASHING", "RUNNING", "RUN_BRAKE") or abs(y) > 0.5:
                    pass
                elif x > want + 2:
                    c.tilt_analog(MAIN, 0.25, 0.5)
                elif x < want - 2:
                    c.tilt_analog(MAIN, 0.75, 0.5)
                elif act == "STANDING":
                    phase, k, seq, last = "run", 0, [], None
                    stocks = a.stock
            elif phase == "run":
                if act != last:
                    seq.append(f"{act}@{k}(y{y:.0f})"); last = act
                if name == "cancel":
                    if k < 3: c.press_button(B.BUTTON_X)
                    if 22 <= k < 25: c.press_button(B.BUTTON_B); c.tilt_analog(MAIN, 0.5, 1.0)
                    if 44 <= k < 47: c.press_button(B.BUTTON_R)
                    if 60 <= k < 63: c.press_button(B.BUTTON_B); c.tilt_analog(MAIN, 0.5, 1.0)
                    done = k > 40 and abs(y) < 0.5 and act in ("STANDING", "LANDING", "LANDING_SPECIAL")
                elif name == "ledge":
                    if not hasattr(main, "fired"):
                        main.fired = False
                    if y > -25 and not main.fired:
                        c.tilt_analog(MAIN, 0.0, 0.5)            # walk/drift off the left edge
                    elif not main.fired:
                        c.press_button(B.BUTTON_B); c.tilt_analog(MAIN, 0.5, 1.0); main.fired = True; main.fk = k
                    else:
                        c.tilt_analog(MAIN, 1.0, 0.5)            # hold toward the stage
                        if k - main.fk in (15, 35):
                            print("capture", name, k - main.fk, r.s.capture_game(f"{prefix}_ledge_{k - main.fk}.png"), flush=True)
                    done = act.startswith("EDGE") or (k > 30 and abs(y) < 0.5 and x > EDGE) or a.stock < stocks
                else:   # homing
                    if k < 3: c.press_button(B.BUTTON_X); c.tilt_analog(MAIN, 0.0, 0.5)
                    if 8 <= k < 11: c.press_button(B.BUTTON_B); c.tilt_analog(MAIN, 0.5, 0.5)
                    if not hasattr(main, "hk"):
                        main.hk = None
                    if k > 12 and main.hk is None and act not in ("LASER_GUN_PULL",):
                        main.hk = k                               # the Homing Attack (incl. end lag) is over
                    if main.hk is not None:
                        d = k - main.hk
                        c.tilt_analog(MAIN, 1.0, 0.5)
                        if d < 3: c.press_button(B.BUTTON_X)
                        if 14 <= d < 17: c.press_button(B.BUTTON_B); c.tilt_analog(MAIN, 0.5, 1.0)
                    done = act.startswith("EDGE") or (k > 30 and abs(y) < 0.5 and x > EDGE) or a.stock < stocks
                k += 1
                if done or k > 400:
                    print(f"SCEN {name:7} | {'DIED' if a.stock < stocks else ('LEDGE' if act.startswith('EDGE') else 'ON STAGE' if abs(y) < 0.5 else 'TIMEOUT')} at x {x:.1f} y {y:.1f} | " + " ".join(seq[:24]), flush=True)
                    for at in ("fired", "fk", "hk"):
                        if hasattr(main, at): delattr(main, at)
                    si += 1; phase, k = "setup", 0
            c.flush()
        print("RESULT: OK" if si == len(SCEN) else f"RESULT: INCOMPLETE ({si})")
    finally:
        r.stop()


if __name__ == "__main__":
    main()
