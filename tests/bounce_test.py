"""Down B in the air (Bounce Attack) three times in a row without landing: prints the peak height after each rebound.

Usage: python bounce_test.py "<iso>" <P1: SONIC or libmelee name> <output prefix>
"""
import sys
import time

from melee import enums

import harness
import runner

B = enums.Button
MAIN = B.BUTTON_MAIN


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
        frames, peaks, peak, last_y, rising, press, seq, last = 0, [], 0.0, 0.0, False, 0, [], None
        t0 = time.time()
        while time.time() - t0 < 60 and frames < 700 and len(peaks) < 4:
            gs = r.s.console.step()
            if gs is None:
                time.sleep(0.001); continue
            if gs.menu_state not in (enums.Menu.IN_GAME, enums.Menu.SUDDEN_DEATH):
                continue
            frames += 1
            a = gs.players[1]
            act = a.action.name if hasattr(a.action, "name") else str(a.action)
            y = float(a.position.y)
            c.release_all()
            k = frames - 150
            if act != last:
                seq.append(f"{act}@{k}"); last = act
            if 0 <= k < 3:
                c.press_button(B.BUTTON_X)
            vy = y - last_y
            if k > 12:
                if vy > 0.5 and not rising and y < 12:        # a rebound has started
                    rising, peak = True, y
                if rising:
                    peak = max(peak, y)
                    if vy < 0:                                 # top of this rebound
                        peaks.append(round(peak, 1)); rising = False
                # press down B whenever he is free in the air and falling or at the top
                if act in ("FALLING", "FALLING_FORWARD", "FALLING_BACKWARD", "JUMPING_FORWARD", "JUMPING_ARIAL_FORWARD") and k > 14 and press == 0:
                    press = 4
            if press > 0:
                c.press_button(B.BUTTON_B); c.tilt_analog(MAIN, 0.5, 0.0)
                press -= 1
            last_y = y
            c.flush()
        print("actions:", " ".join(seq[-30:]))
        print("rebound peak heights:", peaks)
        print("RESULT:", "OK" if len(peaks) >= 3 else "INCOMPLETE")
    finally:
        r.stop()


if __name__ == "__main__":
    main()
