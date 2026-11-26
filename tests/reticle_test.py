"""Homing Attack reticle: walk toward Fox, jump, capture while falling near him.

Usage: python reticle_test.py "<iso>" <P1: SONIC or libmelee name> <output prefix>
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
    harness.WIN = (1280, 1000)
    r = runner.Runner(iso, prefix)
    target = (harness.SONIC_CSS_X, harness.SONIC_CSS_Y) if p1 == "SONIC" else runner.vanilla_css_pos(enums.Character[p1])
    try:
        r.start()
        if not r.go_to_match(target, runner.vanilla_css_pos(enums.Character.FOX)):
            print("RESULT: FAIL (menus)"); return
        c = r.s.c1
        frames, phase, k = 0, "walk", 0
        t0 = time.time()
        while time.time() - t0 < 60 and frames < 600:
            gs = r.s.console.step()
            if gs is None:
                time.sleep(0.001); continue
            if gs.menu_state not in (enums.Menu.IN_GAME, enums.Menu.SUDDEN_DEATH):
                continue
            frames += 1
            a, f = gs.players[1], gs.players[2]
            act = a.action.name if hasattr(a.action, "name") else str(a.action)
            dx = float(f.position.x - a.position.x)
            c.release_all()
            if frames > 130:
                if phase == "walk":
                    if dx > 30:
                        c.tilt_analog(MAIN, 0.75, 0.5)
                    elif act == "STANDING":
                        phase, k = "jump", 0
                elif phase == "jump":
                    if k < 3:
                        c.press_button(B.BUTTON_X)
                    if k in (8, 16, 24, 32):
                        print(f"capture k{k} {act} dx {dx:.1f} y {float(a.position.y):.1f}", r.s.capture_game(f"{prefix}_{k}.png"), flush=True)
                    k += 1
                    if k > 40:
                        break
            c.flush()
        print("RESULT: OK")
    finally:
        r.stop()


if __name__ == "__main__":
    main()
