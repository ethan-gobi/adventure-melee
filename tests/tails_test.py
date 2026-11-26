"""Air up B (Tails carry): jump, press up B at the top, log P1's action and height, capture a few frames.

Usage: python tails_test.py "<iso>" <P1: SONIC or libmelee name> <output prefix>
"""
import sys
import time

from melee import enums

import harness
import runner

B = enums.Button
MAIN = B.BUTTON_MAIN
SHOTS = (6, 20, 40, 58, 75)


def main():
    iso, p1, prefix = sys.argv[1], sys.argv[2], sys.argv[3]
    harness.DISABLE_CODES = ["$Required: Slippi Online"]
    harness.OFFSCREEN = True
    harness.WIN = (1280, 1000)
    r = runner.Runner(iso, prefix)
    r.css_shot = prefix + "_css.png"          # character select screen, once both are picked
    target = (harness.SONIC_CSS_X, harness.SONIC_CSS_Y) if p1 == "SONIC" else runner.vanilla_css_pos(enums.Character[p1])
    try:
        r.start()
        if not r.go_to_match(target, runner.vanilla_css_pos(enums.Character.FOX)):
            print("RESULT: FAIL (menus)"); return
        c = r.s.c1
        frames, k0, seq, last, ys = 0, None, [], None, []
        t0 = time.time()
        while time.time() - t0 < 60 and frames < 520:
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
            if 0 <= k < 4:
                c.press_button(B.BUTTON_X)
            if 22 <= k < 25:
                c.press_button(B.BUTTON_B); c.tilt_analog(MAIN, 0.5, 1.0)
            if k >= 22:
                kk = k - 22
                if act != last:
                    seq.append(f"{act}@{kk}"); last = act
                if kk % 10 == 0:
                    ys.append((kk, round(y, 1)))
                if kk in SHOTS:
                    print("capture", kk, r.s.capture_game(f"{prefix}_{kk}.png"), flush=True)
                if kk > 160:
                    break
            c.flush()
        print("actions:", " ".join(seq))
        print("height by frame:", ys)
        print("RESULT: OK")
    finally:
        r.stop()


if __name__ == "__main__":
    main()
