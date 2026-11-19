"""Measures movement attributes from per-frame game data.

Usage: python measure_attributes.py "<iso>" <P1: SONIC or libmelee name> <output prefix>
P2 is Fox standing still. P1 script (frames counted from the first in-game frame):
  150-189  hold right: dash then run      -> initial dash speed, run speed
  190-249  neutral: slide to a stop       -> traction (per-frame speed loss)
  250      press Y (full jump), then hold left in the air -> jump squat, air speed, gravity, fall speed
Writes <prefix>_frames.csv with every frame and prints the measured values.
"""
import csv
import statistics
import sys
import time

from melee import enums

import harness
import runner

A, Y, MAIN = enums.Button.BUTTON_A, enums.Button.BUTTON_Y, enums.Button.BUTTON_MAIN


def main():
    iso, p1, prefix = sys.argv[1], sys.argv[2], sys.argv[3]
    harness.DISABLE_CODES = ["$Required: Slippi Online"]
    r = runner.Runner(iso, prefix)
    p1_target = (harness.SONIC_CSS_X, harness.SONIC_CSS_Y) if p1 == "SONIC" else runner.vanilla_css_pos(enums.Character[p1])
    rows = []
    try:
        r.start()
        if not r.go_to_match(p1_target, runner.vanilla_css_pos(enums.Character.FOX)):
            print("RESULT: FAIL (menus)")
            return
        c = r.s.c1
        frames = 0
        t = time.time()
        while time.time() - t < 20 and frames < 420:
            gs = r.s.console.step()
            if gs is None:
                time.sleep(0.002)
                continue
            if gs.menu_state not in (enums.Menu.IN_GAME, enums.Menu.SUDDEN_DEATH):
                continue
            frames += 1
            p = gs.players[1]
            act = p.action.name if hasattr(p.action, "name") else str(p.action)
            rows.append(dict(f=frames, char=p.character.name, act=act, af=p.action_frame, x=float(p.position.x), y=float(p.position.y),
                             gx=float(p.speed_ground_x_self), ax=float(p.speed_air_x_self), vy=float(p.speed_y_self), ground=bool(p.on_ground)))
            c.release_all()
            if 150 <= frames < 190:
                c.tilt_analog(MAIN, 1, .5)
            elif 250 <= frames < 254:
                c.press_button(Y)
            elif frames >= 254:
                c.tilt_analog(MAIN, 0, .5)
            c.flush()
    finally:
        r.stop()

    with open(prefix + "_frames.csv", "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        w.writeheader(); w.writerows(rows)

    def acts(name):
        return [row for row in rows if row["act"] == name]

    out = {"character": rows[0]["char"], "frames": len(rows)}
    dash = acts("DASHING")
    out["dash_first_frame_speed"] = round(abs(dash[0]["gx"]), 4) if dash else None
    run = [row for row in rows if 150 <= row["f"] < 190 and row["act"] == "RUNNING"]
    out["run_speed_max"] = round(max(abs(row["gx"]) for row in run), 4) if run else None
    slide = [row for row in rows if 191 <= row["f"] < 250 and row["ground"] and abs(row["gx"]) > 0.05]
    drops = [abs(a["gx"]) - abs(b["gx"]) for a, b in zip(slide, slide[1:]) if abs(b["gx"]) > 0.05]
    out["traction_median_drop"] = round(statistics.median(drops), 4) if drops else None
    knee = acts("KNEE_BEND")
    out["jump_squat_frames"] = len(knee)
    air = [row for row in rows if row["f"] >= 254 and not row["ground"]]
    out["air_speed_max"] = round(max(abs(row["ax"]) for row in air), 4) if air else None
    vys = [row["vy"] for row in air]
    out["fall_speed_max"] = round(-min(vys), 4) if vys else None
    falling = [b - a for a, b in zip(vys, vys[1:]) if -min(vys) - 0.01 > -b and b < a]
    out["gravity_median"] = round(-statistics.median(falling), 4) if falling else None
    for k, v in out.items():
        print(f"MEASURED {k} = {v}", flush=True)
    print("RESULT: OK", flush=True)


if __name__ == "__main__":
    main()
