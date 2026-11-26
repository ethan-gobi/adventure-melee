"""Soak test for the out-of-memory crash: a long match with Sonic doing a rotating list of moves every 40 frames.
Reports the frame count, any stall (no frames for 10 s = crash/hang) and what was used last.
Usage: python soak_test.py "<iso>" <P1: SONIC or libmelee name> <output prefix> [seconds, default 600]
"""
import sys
import time

from melee import enums

import harness
import runner

B = enums.Button
MAIN, CST = B.BUTTON_MAIN, B.BUTTON_C
SEQ = [("jab", lambda c: c.press_button(B.BUTTON_A)), ("ftilt", lambda c: (c.tilt_analog(MAIN, 0.8, 0.5), c.press_button(B.BUTTON_A))),
       ("usmash", lambda c: c.tilt_analog(CST, 0.5, 1.0)), ("fsmash", lambda c: c.tilt_analog(CST, 1.0, 0.5)), ("dsmash", lambda c: c.tilt_analog(CST, 0.5, 0.0)),
       ("homing", lambda c: c.press_button(B.BUTTON_B)), ("jump", lambda c: c.press_button(B.BUTTON_X)), ("tails", lambda c: (c.press_button(B.BUTTON_B), c.tilt_analog(MAIN, 0.5, 1.0))),
       ("crouch", lambda c: c.tilt_analog(MAIN, 0.5, 0.0)), ("shield", lambda c: c.press_button(B.BUTTON_R)), ("grab", lambda c: c.press_button(B.BUTTON_Z)),
       ("spindash", lambda c: (c.press_button(B.BUTTON_B), c.tilt_analog(MAIN, 0.5, 0.0))), ("taunt", lambda c: c.press_button(B.BUTTON_D_UP)),
       ("walk", lambda c: c.tilt_analog(MAIN, 0.2, 0.5)), ("walk", lambda c: c.tilt_analog(MAIN, 0.8, 0.5))]


def main():
    iso, p1, prefix = sys.argv[1], sys.argv[2], sys.argv[3]
    secs = float(sys.argv[4]) if len(sys.argv) > 4 else 600
    harness.DISABLE_CODES = ["$Required: Slippi Online"]
    harness.OFFSCREEN = True
    r = runner.Runner(iso, prefix)
    target = (harness.SONIC_CSS_X, harness.SONIC_CSS_Y) if p1 == "SONIC" else runner.vanilla_css_pos(enums.Character[p1])
    try:
        r.start()
        if not r.go_to_match(target, runner.vanilla_css_pos(enums.Character.FOX)):
            print("RESULT: FAIL (menus)"); return
        c = r.s.c1
        frames, lastgs, t0, used, held, last_menu = 0, time.time(), time.time(), [], 0, None
        while time.time() - t0 < secs:
            gs = r.s.console.step()
            if gs is None:
                if time.time() - lastgs > 10:
                    print(f"STALL: no frames for 10 s after {frames} in-game frames ({frames / 60:.0f} s of play); last moves {used[-6:]}", flush=True)
                    try:
                        print("capture", r.s.capture_game(prefix + "_stall.png"), flush=True)
                    except Exception as e:
                        print("capture failed", e)
                    print("RESULT: STALL"); return
                time.sleep(0.002); continue
            lastgs = time.time()
            if gs.menu_state != last_menu:
                print(f"[{time.time() - t0:6.0f}s] menu {gs.menu_state.name} after {frames} frames", flush=True); last_menu = gs.menu_state
            if gs.menu_state not in (enums.Menu.IN_GAME, enums.Menu.SUDDEN_DEATH):
                continue
            frames += 1
            c.release_all()
            x = float(gs.players[1].position.x)
            if frames > 120 and abs(x) > 40 and abs(float(gs.players[1].position.y)) < 1:
                c.tilt_analog(MAIN, 0.0 if x > 0 else 1.0, 0.5)     # stay near the middle so he does not self-destruct
            elif frames > 120:
                i = (frames // 40) % len(SEQ)
                if frames % 40 < 6:
                    SEQ[i][1](c)
                    if frames % 40 == 0:
                        used.append(SEQ[i][0])
                elif SEQ[i][0] in ("shield", "crouch", "spindash") and frames % 40 < 30:
                    SEQ[i][1](c)
            if frames % 3600 == 0:
                print(f"[{time.time() - t0:6.0f}s] {frames} frames ({frames / 3600:.0f} min of play), P1 stocks {gs.players[1].stock}, P2 stocks {gs.players[2].stock}", flush=True)
            c.flush()
        print(f"RESULT: OK ({frames} in-game frames, {frames / 3600:.1f} min of play, no stall)")
    finally:
        r.stop()


if __name__ == "__main__":
    main()
