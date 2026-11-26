"""Menu navigation by direct memory reads, with no injected menu codes and no button mashing.

Every A press on the main menu is gated on what memory says is highlighted, so the bot can
never confirm "Online Play" (which opens a browser login page).

Usage: python runner.py "<iso>" <P1: SONIC or libmelee character name> <output prefix>
"""
import os
import sys
import time

import melee
from melee import enums

import harness
from mem import GameMemory

harness.GECKO = False

A, B, START = enums.Button.BUTTON_A, enums.Button.BUTTON_B, enums.Button.BUTTON_START
MAIN = enums.Button.BUTTON_MAIN
FD_CURSOR = (6.7, -9.0)


def vanilla_css_pos(character):
    idx = enums.from_internal(character)
    row, col = idx // 9, idx % 9
    if row == 2:
        col += 1
    return (-32.5 + 3.5 + col * 7.0, 1 + 3.5 + (2 - row) * 7.0)


class Pulse:
    """Press a button (or tilt the stick) briefly, then force a release gap before the next press."""

    def __init__(self, hold=0.07, gap=0.20):
        self.hold, self.gap, self.t = hold, gap, 0.0
        self.active = None

    def ready(self):
        return time.time() - self.t > self.hold + self.gap

    def fire(self, fn):
        self.t = time.time()
        self.active = fn

    def apply(self):
        if self.active and time.time() - self.t <= self.hold:
            self.active()


class Runner:
    def __init__(self, iso, prefix):
        self.s = harness.Session(iso, prefix + ".csv")
        self.s.console_kwargs = {"polling_mode": True}
        self.prefix = prefix
        self.t0 = time.time()
        self.events = []

    def say(self, *a):
        line = f"[{time.time() - self.t0:5.1f}s] " + " ".join(str(x) for x in a)
        self.events.append(line)
        print(line, flush=True)

    def start(self):
        self.s.start(connect_slippi=False)
        self.m = GameMemory(self.s.pid)
        while not self.m.find():
            time.sleep(0.3)
            if time.time() - self.t0 > 40:
                raise SystemExit("emulated memory not found")
        self.say("memory found")
        self.crash_watch()
        self.slippi = self.s.console.connect()
        self.say("slippi stream connected:", self.slippi)

    def crash_watch(self):
        """Independent thread: input writes block if Dolphin freezes, so watch for its crash dialog separately."""
        import threading
        self.crashed = False

        def run():
            while not self.crashed and self.s.console is not None:
                time.sleep(1)
                try:
                    if self.warning_dialog():
                        self.crashed = True
                        self.say("CRASH: Dolphin warning dialog (scene", self.scene(), ")")
                        self.s.screenshot(self.prefix + "_crash.png")
                        try:
                            if getattr(self, 'on_crash', None): self.on_crash(self)
                        except Exception as e:
                            self.say('on_crash error', repr(e))
                        self.s.console._process.kill()  # unblocks pipe writes; only our own Dolphin
                except Exception as e:
                    self.say("crash_watch error", e)
        threading.Thread(target=run, daemon=True).start()

    def stop(self):
        self.s.stop()

    def scene(self):
        w = self.m.u32(0x80479D30) or 0
        return (w >> 24) & 0xFF, w & 0xFF  # major, minor

    def css_cursor(self, port):
        p = self.m.u32(0x804A0BC0 + 4 * (port - 1))
        if not p or not self.m.valid(p, 0x14):
            return None
        return self.m.f32(p + 0xC), self.m.f32(p + 0x10)

    def sss_cursor(self):
        p = self.m.u32(0x804D7820)
        for off in (0x10, 0x28):
            if not p or not self.m.valid(p + off, 4):
                return None
            p = self.m.u32(p + off)
        if not p or not self.m.valid(p, 0x40):
            return None
        x, y = self.m.f32(p + 0x38), self.m.f32(p + 0x3C)
        import math
        if x is None or y is None or not (math.isfinite(x) and math.isfinite(y)) or abs(x) > 60 or abs(y) > 60:
            return None  # chain points somewhere that is not a stage cursor (m-ex)
        return x, y

    def warning_dialog(self):
        import win32gui, win32process
        found = []

        def cb(h, _):
            if win32gui.IsWindowVisible(h) and win32gui.GetWindowText(h) == "Warning" and win32process.GetWindowThreadProcessId(h)[1] == self.s.pid:
                found.append(h)
        win32gui.EnumWindows(cb, None)
        return bool(found)

    def snapshot(self):
        import numpy as np
        raw = self.m.read(0x80000000, 0x1800000)
        if raw is None:
            raise RuntimeError("RAM read failed")
        with np.errstate(all="ignore"):
            return np.frombuffer(raw, dtype=">f4").astype("float64")

    def nudge(self, c, x, y, secs=0.3):
        t = time.time()
        while time.time() - t < secs:
            c.tilt_analog(MAIN, x, y); c.flush(); time.sleep(0.01)
        c.release_all(); c.flush(); time.sleep(0.35)

    def find_sss_cursor(self, c):
        try:
            return self._find_sss_cursor(c)
        except Exception as e:
            import traceback
            self.say("find_sss_cursor failed:", repr(e)); traceback.print_exc()
            return None

    def _find_sss_cursor(self, c):
        import numpy as np
        self.say("searching RAM for the stage cursor")
        c.release_all(); c.flush(); time.sleep(0.6)
        s0 = self.snapshot(); self.nudge(c, 1, .5)
        s1 = self.snapshot(); self.nudge(c, .5, 1)
        s2 = self.snapshot(); self.nudge(c, 0, .5)
        s3 = self.snapshot()
        with np.errstate(invalid="ignore"):
            dx1, dy1 = s1[:-1] - s0[:-1], s1[1:] - s0[1:]
            dx2, dy2 = s2[:-1] - s1[:-1], s2[1:] - s1[1:]
            dx3 = s3[:-1] - s2[:-1]
            ok = ((dx1 > 0.5) & (dx1 < 40) & (np.abs(dy1) < 1e-6) &
                  (np.abs(dx2) < 1e-6) & (dy2 > 0.5) & (dy2 < 40) &
                  (dx3 < -0.5) & (dx1 < 40) & (dy2 < 40) & (dx3 > -40))
            for snap in (s0, s1, s2, s3):  # every sample must be a plausible screen coordinate
                ok &= np.isfinite(snap[:-1]) & np.isfinite(snap[1:]) & (np.abs(snap[:-1]) < 40) & (np.abs(snap[1:]) < 30)
        idx = np.nonzero(ok)[0]
        cands = [(0x80000000 + 4 * int(i), round(float(s3[i]), 2), round(float(s3[i + 1]), 2)) for i in idx[:12]]
        self.say("stage cursor candidates (addr, x, y):", [(hex(a), x, y) for a, x, y in cands])
        if not cands:
            return None
        # verify: pushing the stick down must lower y and leave x alone
        # verify each candidate twice: stick down must lower y only, then stick right must raise x only
        b1 = {a: (self.m.f32(a), self.m.f32(a + 4)) for a, _, _ in cands}
        self.nudge(c, .5, 0)
        b2 = {a: (self.m.f32(a), self.m.f32(a + 4)) for a, _, _ in cands}
        self.nudge(c, 1, .5)
        b3 = {a: (self.m.f32(a), self.m.f32(a + 4)) for a, _, _ in cands}
        for a, _, _ in cands:
            (x0, y0), (x1, y1), (x2, y2) = b1[a], b2[a], b3[a]
            if y1 < y0 - 0.5 and abs(x1 - x0) < 1e-4 and x2 > x1 + 0.5 and abs(y2 - y1) < 1e-4:
                self.say(f"verified stage cursor at {hex(a)}")
                return a
        self.say("no candidate passed the down-nudge check")
        return None

    def steer(self, c, cur, target, tol=1.2):
        """Tilt the stick toward target. Returns True when inside tolerance (stick neutral)."""
        dx, dy = target[0] - cur[0], target[1] - cur[1]
        if abs(dx) <= tol and abs(dy) <= tol:
            c.tilt_analog(MAIN, .5, .5)
            return True
        # slow down when close so we do not overshoot
        def axis(d):
            if abs(d) <= tol:
                return .5
            mag = .5 if abs(d) > 6 else .25
            return .5 + mag if d > 0 else .5 - mag
        c.tilt_analog(MAIN, axis(dx), axis(dy))
        return False

    def go_to_match(self, p1_target, p2_target, timeout=110):
        """Main menu -> VS -> character select -> stage select -> in game. Returns True when in game."""
        c1, c2 = self.s.c1, self.s.c2
        pulse = Pulse()
        picked = {1: False, 2: False}
        on_target_since = {1: None, 2: None}
        last = None
        last_dialog_check = 0
        sss_on = None
        t_end = time.time() + timeout
        while time.time() < t_end and not self.crashed:
            major, minor = self.scene()
            if (major, minor) != last:
                self.say(f"scene major={major} minor={minor}")
                last = (major, minor)
                picked = {1: False, 2: False}
                sss_on = None
            if time.time() - last_dialog_check > 1.0:
                last_dialog_check = time.time()
                _t = time.time(); _wd = self.warning_dialog()
                if time.time() - _t > 0.5:
                    self.say(f"warning_dialog() took {time.time() - _t:.1f}s")
                if _wd:
                    self.say("DOLPHIN WARNING DIALOG (game crashed)")
                    self.s.screenshot(self.prefix + "_crash.png")
                    return False
            c1.release_all(); c2.release_all()
            if major == 2 and minor == 2:
                c1.flush(); c2.flush()
                return True
            if major == 1:
                sub, sel = self.m.u8(0x804A04F0), self.m.u8(0x804A04F3)
                if pulse.ready():
                    if sub == 0:
                        if sel == 1:
                            self.say("main menu: VS Mode highlighted -> A"); pulse.fire(lambda: c1.press_button(A))
                        else:
                            self.say(f"main menu: selection {sel} -> down"); pulse.fire(lambda: c1.tilt_analog(MAIN, .5, 0))
                    elif sub == 2:
                        if sel == 0:
                            self.say("VS menu: Melee highlighted -> A"); pulse.fire(lambda: c1.press_button(A))
                        else:
                            self.say(f"VS menu: selection {sel} -> up"); pulse.fire(lambda: c1.tilt_analog(MAIN, .5, 1))
                    else:
                        self.say(f"unexpected submenu {sub} -> B"); pulse.fire(lambda: c1.press_button(B))
                pulse.apply()
            elif major == 2 and minor == 0:
                for port, c, target in ((1, c1, p1_target), (2, c2, p2_target)):
                    cur = self.css_cursor(port)
                    if cur is None or picked[port]:
                        continue
                    if self.steer(c, cur, target):
                        if on_target_since[port] is None:
                            on_target_since[port] = time.time()
                        elif time.time() - on_target_since[port] > 0.25:
                            # one single A press per port, held for a few frames
                            self.say(f"port {port} at {tuple(round(v, 1) for v in cur)} -> A")
                            t = time.time()
                            while time.time() - t < 0.08:
                                c.press_button(A); c.flush(); time.sleep(0.01)
                            c.release_all(); c.flush()
                            picked[port] = True
                            self.picked_time = time.time()
                    else:
                        on_target_since[port] = None
                if picked[1] and picked[2] and time.time() - self.picked_time > 3.0:
                    self.say("START did not start the match; picking again")
                    picked = {1: False, 2: False}
                    on_target_since = {1: None, 2: None}
                elif picked[1] and picked[2] and time.time() - self.picked_time > 0.8 and pulse.ready():
                    slots = [self.m.read(0x803F0E08 + 0x24 * i, 4).hex() for i in range(2)]
                    self.say("both picked, slot bytes", slots, "-> START")
                    if getattr(self, "css_shot", None) and not getattr(self, "_css_done", False):
                        self._css_done = True
                        time.sleep(0.8)
                        self.say("css capture", self.s.capture_game(self.css_shot))
                    pulse.fire(lambda: c1.press_button(START))
                pulse.apply()
            elif major == 2 and minor == 1:
                _t = time.time()
                cur = None if getattr(self, 'sss_addr', None) is not None else self.sss_cursor()
                if time.time() - _t > 0.5:
                    self.say(f'sss_cursor() took {time.time() - _t:.1f}s')
                if getattr(self, '_sss_logged', None) is None:
                    self._sss_logged = True; self.say('stage select: vanilla chain gives', cur)
                if cur is None and getattr(self, "sss_addr", None) is None:
                    # m-ex rebuilds the stage select, so the vanilla pointer chain does not reach the cursor.
                    # Find it by diffing RAM while nudging the stick (A is never pressed here).
                    self.sss_addr = self.find_sss_cursor(c1)
                    if self.sss_addr is None:
                        self.say("stage cursor not found; pressing A where the cursor is (selects some stage)")
                        for _ in range(6):
                            c1.press_button(A); c1.flush(); time.sleep(0.02)
                        c1.release_all(); c1.flush()
                        self.sss_addr = 0
                    sss_on = None
                if cur is None and self.sss_addr:
                    cur = (self.m.f32(self.sss_addr), self.m.f32(self.sss_addr + 4))
                if cur is None:
                    pass
                else:
                    if self.steer(c1, cur, FD_CURSOR, tol=1.0):
                        if sss_on is None:
                            sss_on = time.time()
                        elif time.time() - sss_on > 0.4 and pulse.ready():
                            self.say(f"stage cursor at {tuple(round(v, 1) for v in cur)}, hovered stage byte {self.m.u8(0x804D6CAD)} -> A")
                            pulse.fire(lambda: c1.press_button(A))
                    else:
                        sss_on = None
                    pulse.apply()
            c1.flush(); c2.flush()
            time.sleep(1 / 120)
        self.say("TIMEOUT in menus")
        return False


def main():
    iso, p1, prefix = sys.argv[1], sys.argv[2], sys.argv[3]
    harness.DISABLE_CODES = [a.split('=', 1)[1] for a in sys.argv[4:] if a.startswith('--disable=')]
    harness.DUMP_FRAMES = '--dump' in sys.argv
    harness.OFFSCREEN = '--capture' in sys.argv
    r = Runner(iso, prefix)
    p1_target = (harness.SONIC_CSS_X, harness.SONIC_CSS_Y) if p1 == "SONIC" else vanilla_css_pos(enums.Character[p1])
    result = "FAIL"
    try:
        r.start()
        if r.go_to_match(p1_target, vanilla_css_pos(enums.Character.FOX)):
            r.say("IN GAME")
            frames = 0
            t = time.time()
            c = r.s.c1
            while time.time() - t < 14 and frames < 480:
                gs = r.s.console.step()
                if gs is not None:
                    r.last_gs_time = time.time()
                elif harness.OFFSCREEN and frames > 0 and not getattr(r, 'stall_capture', None) and time.time() - getattr(r, 'last_gs_time', time.time()) > 3:
                    r.stall_capture = True
                    import psutil
                    r.say(f"STALL after frame {frames}: no frames for 3s, dolphin cpu% {psutil.Process(r.s.pid).cpu_percent(interval=1.0)}")
                    r.say("  capture:", r.s.capture_game(prefix + "_stall.png"))
                    r.s.screenshot(prefix + "_stallwin.png")
                if gs is None and harness.OFFSCREEN and frames == 0 and time.time() - t > 6 and not getattr(r, 'no_frame_since', None):
                    r.no_frame_since = time.time()
                    import psutil
                    pr = psutil.Process(r.s.pid)
                    r.say(f"no in-game frames after 6s; dolphin cpu% {pr.cpu_percent(interval=1.0)} responding windows:")
                    r.say("  capture:", r.s.capture_game(prefix + "_stall.png"))
                    r.s.screenshot(prefix + "_stallwin.png")
                if gs is None:
                    if r.warning_dialog():
                        r.say("DOLPHIN WARNING DIALOG in game"); r.s.screenshot(prefix + "_crash.png"); break
                    time.sleep(0.002)
                    continue
                if gs.menu_state not in (enums.Menu.IN_GAME, enums.Menu.SUDDEN_DEATH):
                    continue
                frames += 1
                r.s.log(gs)
                p = gs.players.get(1)
                if frames == 1:
                    r.say("first frame: stage", gs.stage, "| p1", p.character.name, "| unknown char ids", sorted(set(harness.UNKNOWN_CHARACTER_IDS)), "| p2", gs.players[2].character.name)
                c.release_all()
                if '--homing' in sys.argv:
                    fox = gs.players[2]
                    dxf = float(fox.position.x - p.position.x)
                    st = getattr(r, 'hstate', 'walk')
                    if frames >= 130 and st == 'walk':
                        if dxf > 40:
                            c.tilt_analog(MAIN, 1, .5)
                        else:
                            r.hstate, r.hframe = 'press', frames
                            r.say(f"  homing: B at frame {frames}, Fox {dxf:.1f} units ahead")
                    if st == 'press' and frames - r.hframe < 3:
                        c.press_button(enums.Button.BUTTON_B)
                    if st == 'press' and frames - r.hframe <= 45:
                        r.say(f"  H f+{frames - r.hframe:2}: p1 {p.action.name if hasattr(p.action,'name') else p.action} pos=({p.position.x:.1f},{p.position.y:.1f}) | fox {fox.action.name if hasattr(fox.action,'name') else fox.action} pos=({fox.position.x:.1f},{fox.position.y:.1f}) pct {fox.percent}")
                    c.flush()
                    continue
                if 200 <= frames < 203:
                    c.press_button(enums.Button.BUTTON_B if '--special' in sys.argv else A)
                elif 260 <= frames < 290:
                    c.tilt_analog(MAIN, 1, .5)
                elif 320 <= frames < 323:
                    c.press_button(enums.Button.BUTTON_Y)
                elif 330 <= frames < 333:
                    c.press_button(A)
                c.flush()
                if harness.OFFSCREEN and frames in (100, 204, 275, 335, 345):
                    res = r.s.capture_game(f"{prefix}_shot_{frames}.png")
                    r.say(f"captured frame {frames}: {res}")
                if '--special' in sys.argv and 198 <= frames <= 240 and frames % 3 == 0:
                    r.say(f"  B-test frame {frames}: p1 {p.action} af={p.action_frame} pos=({p.position.x:.1f},{p.position.y:.1f}) | fox x {gs.players[2].position.x:.1f} pct {gs.players[2].percent}")
                if frames % 80 == 0:
                    r.say(f"frame {frames}: p1 {p.action} af={p.action_frame} pos=({p.position.x:.1f},{p.position.y:.1f})")
            r.say("in-game frames received:", frames)
            if frames >= 480:
                result = "OK"
    finally:
        dd = getattr(r.s, 'dump_dir', None)
        if dd and os.path.isdir(dd):
            import shutil
            keep = prefix + '_frames'
            os.makedirs(keep, exist_ok=True)
            files = sorted(os.listdir(dd))
            for fn in files[-600::40]:
                shutil.copy(os.path.join(dd, fn), keep)
            print('frames dumped:', len(files), '-> kept', len(files[-600::40]), 'in', keep, flush=True)
        r.stop()
    print("RESULT:", result, flush=True)


if __name__ == "__main__":
    main()
