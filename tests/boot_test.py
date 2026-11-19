"""Boot test: does the build start, can Sonic be picked, does a match on Final Destination load?

Usage: python boot_test.py "<iso>" <log.csv>
Port 1 = Sonic (bot), port 2 = Fox standing still. Sonic then does a few basic actions.
"""
import sys
import time

import melee
from melee import enums

import harness


def main():
    iso, log_path = sys.argv[1], sys.argv[2]
    P1_CHAR = sys.argv[3] if len(sys.argv) > 3 else 'SONIC'
    harness.GECKO = 'nogecko' not in sys.argv
    s = harness.Session(iso, log_path)
    mh = melee.MenuHelper()
    t0 = time.time()
    ingame_frames = 0
    seen_menus = []
    css_frames = 0
    result = "TIMEOUT"
    try:
        s.start()
        s.watchdog(log_path.replace('.csv', '_stall.png'))
        while time.time() - t0 < 150:
            try:
                gs = s.console.step()
            except Exception as e:
                print('step ended:', type(e).__name__, flush=True); result = 'STALL'; break
            if getattr(s, 'stalled', False):
                result = 'STALL'; break
            if gs is None:
                continue
            s.log(gs)
            if not seen_menus or seen_menus[-1] != gs.menu_state.name:
                seen_menus.append(gs.menu_state.name)
                print(f"[{time.time() - t0:5.1f}s] menu ->", gs.menu_state.name, flush=True)
            if gs.menu_state in (enums.Menu.IN_GAME, enums.Menu.SUDDEN_DEATH):
                ingame_frames += 1
                p1 = gs.players.get(1)
                if ingame_frames == 1:
                    print("IN GAME. stage:", gs.stage, "| p1 char:", p1.character.name, "| unknown char ids seen:", sorted(set(harness.UNKNOWN_CHARACTER_IDS)), flush=True)
                f = ingame_frames
                c = s.c1
                c.release_all()
                # simple script: wait, jab, dash right, jump, neutral air
                if 200 <= f < 203:
                    c.press_button(enums.Button.BUTTON_A)
                elif 260 <= f < 290:
                    c.tilt_analog(enums.Button.BUTTON_MAIN, 1, .5)
                elif 320 <= f < 323:
                    c.press_button(enums.Button.BUTTON_Y)
                elif 330 <= f < 333:
                    c.press_button(enums.Button.BUTTON_A)
                if f % 60 == 0:
                    print(f"  frame {f}: p1 {p1.action} af={p1.action_frame} pos=({p1.position.x:.1f},{p1.position.y:.1f})", flush=True)
                if f >= 480:
                    result = "OK"
                    break
            elif gs.menu_state == enums.Menu.CHARACTER_SELECT:
                css_frames += 1
                p1 = gs.players.get(1)
                p2 = gs.players.get(2)
                if css_frames % 30 == 1 and p1 is not None:
                    print('   p2:', None if p2 is None else (round(float(p2.cursor.x),1), round(float(p2.cursor.y),1), p2.controller_status, p2.cpu_level), 'ports:', list(gs.players.keys()), flush=True)
                    print(f"  css: p1 cursor=({p1.cursor.x:.1f},{p1.cursor.y:.1f}) coin_down={p1.coin_down} char={p1.character.name} | p2 coin_down={p2.coin_down if p2 else None} char={p2.character.name if p2 else None}", flush=True)
                sonic_ready = s.pick_sonic(gs, s.c1) if P1_CHAR == 'SONIC' else s.pick_vanilla(gs, s.c1, enums.Character[P1_CHAR])
                fox_ready = s.pick_vanilla(gs, s.c2, enums.Character.FOX)
                if sonic_ready and fox_ready:
                    if gs.frame % 2 == 0:
                        s.c1.press_button(enums.Button.BUTTON_START)
                    else:
                        s.c1.release_all()
            elif gs.menu_state == enums.Menu.STAGE_SELECT:
                mh.choose_stage(enums.Stage.FINAL_DESTINATION, gs, s.c1, enums.Character.FOX, autostart=True)
                s.c2.release_all()
            else:
                mh.choose_versus_mode(gs, s.c1)
                s.c2.release_all()
    finally:
        s.stop()
    print("RESULT:", result, "| menus seen:", seen_menus, "| in-game frames:", ingame_frames, flush=True)


if __name__ == "__main__":
    main()
