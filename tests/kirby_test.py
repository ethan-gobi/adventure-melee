"""Kirby (P1, bot) inhales standing Sonic (P2), swallows to copy, then uses the copied neutral B."""
import sys, time
from melee import enums
import harness, runner
B, MAIN = enums.Button.BUTTON_B, enums.Button.BUTTON_MAIN

def dump(r):
    m = r.m
    ok = lambda a: a is not None and 0x80000000 <= a < 0x81800000
    for port in (0, 1):
        g = m.u32(0x80453080 + port * 0xE90 + 0xB0)
        if not ok(g): r.say(f'port {port+1}: no fighter gobj ({g})'); continue
        fd = m.u32(g + 0x2C)
        if not ok(fd): r.say(f'port {port+1}: no fighter data'); continue
        kind = m.u32(fd + 0x4); lookup = m.u32(fd + 0x5F0); tnum = m.u32(fd + 0x5AC)
        ptrs = [m.u32(lookup + 4 * i) for i in range(90)] if ok(lookup) else []
        valid = [i for i, p in enumerate(ptrs) if ok(p)]
        firstbad = next((i for i, p in enumerate(ptrs) if not ok(p)), None)
        r.say(f'port {port+1}: kind {kind} dobj_lookup {hex(lookup) if lookup else lookup} toggle_num {tnum} | first invalid entry index {firstbad} | sample {[hex(p) for p in ptrs[max(0,(firstbad or 0)-2):(firstbad or 0)+4]]}')
        toggles = [(m.u8(fd + 0x5F4 + i * 2), m.u8(fd + 0x5F5 + i * 2)) for i in range(12)]
        r.say(f'   dobj_toggle bytes {toggles}')

def main():
    iso, prefix = sys.argv[1], sys.argv[2]
    harness.DISABLE_CODES = ["$Required: Slippi Online"]; harness.OFFSCREEN = True
    r = runner.Runner(iso, prefix); result = "FAIL"
    try:
        r.start()
        r.on_crash = dump
        pos = lambda n: (harness.SONIC_CSS_X, harness.SONIC_CSS_Y) if n == 'SONIC' else runner.vanilla_css_pos(enums.Character[n])
        p1n = sys.argv[3] if len(sys.argv) > 3 else 'KIRBY'; p2n = sys.argv[4] if len(sys.argv) > 4 else 'SONIC'
        loadonly = len(sys.argv) > 3
        if not r.go_to_match(pos(p1n), pos(p2n)):
            print("RESULT: FAIL (menus)"); return
        c = r.s.c1; frames = 0; phase = "walk"; tp = 0; last = None; t = time.time()
        while time.time() - t < 45 and not r.crashed:
            gs = r.s.console.step()
            if gs is None:
                time.sleep(0.002); continue
            if gs.menu_state not in (enums.Menu.IN_GAME, enums.Menu.SUDDEN_DEATH): continue
            frames += 1
            k, s = gs.players[1], gs.players[2]
            ka = k.action.name if hasattr(k.action, "name") else str(k.action)
            sa = s.action.name if hasattr(s.action, "name") else str(s.action)
            if (phase, ka, sa) != last:
                last = (phase, ka, sa); r.say(f"f{frames} {phase} kirby {ka} | sonic {sa}")
            c.release_all(); dx = float(s.position.x - k.position.x)
            if loadonly and frames >= 150: result = 'OK'; break
            if frames < 130: pass
            elif phase == "walk":
                if dx > 11: c.tilt_analog(MAIN, 1, .5)
                else: phase, tp = "inhale", frames
            elif phase == "inhale":
                if frames - tp < 50: c.press_button(B)
                if frames - tp > 80: phase, tp = "swallow", frames
            elif phase == "swallow":
                if frames - tp < 6: c.tilt_analog(MAIN, .5, 0)
                if frames - tp > 130: phase, tp = "use", frames
            elif phase == "use":
                if frames - tp < 4: c.press_button(B)
                if frames - tp > 150: result = "OK"; break
            c.flush()
        r.say("frames", frames, "crashed", r.crashed)
    finally:
        r.stop()
    print("RESULT:", result, flush=True)

if __name__ == "__main__":
    main()
