"""Close-ups of P1's face in game, using the pause camera (it centres on the player who paused and can zoom and turn).

Usage: python face_test.py "<iso>" <P1: SONIC or libmelee name> <output prefix>
Three passes: standing, mid forward smash (mouth open) and mid jab. Each pauses, zooms in (Y) and captures from the
default side-on angle and after turning the camera toward his face (C-stick).
"""
import sys
import time

from melee import enums

import harness
import runner

B = enums.Button
MAIN, CSTICK = B.BUTTON_MAIN, B.BUTTON_C


def hold(r, secs, fn=None):
    """keep inputs held while the game is paused (no frames arrive, so this is timed)"""
    c = r.s.c1
    t = time.time()
    while time.time() - t < secs:
        c.release_all()
        if fn:
            fn(c)
        c.flush()
        r.s.console.step()
        time.sleep(0.012)
    c.release_all(); c.flush()


def main():
    iso, p1, prefix = sys.argv[1], sys.argv[2], sys.argv[3]
    harness.DISABLE_CODES = ["$Required: Slippi Online"]
    harness.OFFSCREEN = True
    harness.WIN = (1280, 1000)
    r = runner.Runner(iso, prefix)
    target = (harness.SONIC_CSS_X, harness.SONIC_CSS_Y) if p1 == "SONIC" else runner.vanilla_css_pos(enums.Character[p1])
    passes = [("idle", None, 0), ("fsmash", lambda c: c.tilt_analog(CSTICK, 1.0, 0.5), 17)]
    try:
        r.start()
        if not r.go_to_match(target, runner.vanilla_css_pos(enums.Character.FOX)):
            print("RESULT: FAIL (menus)"); return
        c = r.s.c1
        frames, pi, k = 0, 0, -1
        t0 = time.time()
        while time.time() - t0 < 200 and pi < len(passes):
            gs = r.s.console.step()
            if gs is None:
                time.sleep(0.001); continue
            if gs.menu_state not in (enums.Menu.IN_GAME, enums.Menu.SUDDEN_DEATH):
                continue
            frames += 1
            name, act, at = passes[pi]
            c.release_all()
            if frames < 150:
                c.flush(); continue
            k += 1
            if act and k < 2:
                act(c)
            if k == at:
                c.press_button(B.BUTTON_START); c.flush()
                time.sleep(0.05)
                hold(r, 0.6)
                print("capture", name, "paused", r.s.capture_game(f"{prefix}_{name}_0.png"), flush=True)
                for step in (1, 2, 3):             # zoom in a little at a time (Y zooms in, X out); 0.9 s goes right through him
                    hold(r, 0.11, lambda c_: c_.press_button(B.BUTTON_Y))
                    hold(r, 0.15)
                print("capture", name, "zoomed", r.s.capture_game(f"{prefix}_{name}_z.png"), flush=True)
                for tag, cx in (("R", 1.0), ("L", 0.0)):       # turn the camera a step at a time, first one way then the other
                    for step in range(1, (7 if tag == "R" else 19)):
                        hold(r, 0.09, lambda c_: c_.tilt_analog(MAIN, cx, 0.5))      # control stick orbits; the C-stick only pans
                        hold(r, 0.12)
                        if tag == "R" or step > 6:
                            print("capture", name, tag, step, r.s.capture_game(f"{prefix}_{name}_{tag}{step}.png"), flush=True)
                seen = False
                for _ in range(4):                 # unpause, and make sure frames are arriving again
                    c.press_button(B.BUTTON_START); c.flush()
                    time.sleep(0.08)
                    c.release_all(); c.flush()
                    t1 = time.time()
                    while time.time() - t1 < 0.6:
                        if r.s.console.step() is not None:
                            seen = True
                            break
                    if seen:
                        break
                pi, k, frames = pi + 1, -1, 60          # 90 frames of rest before the next pass
                continue
            c.flush()
        print("RESULT:", "OK" if pi == len(passes) else f"INCOMPLETE ({pi}/{len(passes)})")
    finally:
        r.stop()


if __name__ == "__main__":
    main()
