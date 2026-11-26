"""Shared libmelee test harness for the Sonic builds.

- Launches Slippi Dolphin from a temporary user folder (the real Dolphin config is never touched).
- Uses its own Slippi port, starts minimized without taking focus.
- Refuses to run if another Dolphin is already open (the bot pipes are shared machine-wide).
- Only ever stops the Dolphin process it started itself.
"""
import csv
import os
import subprocess
import sys
import time

import melee
import psutil
from melee import enums

SLIPPI_DIR = os.path.join(os.environ["APPDATA"], "Slippi Launcher", "netplay")
SLIPPI_PORT = 51447
GECKO = True
DUMP_FRAMES = False
WIN = (640, 528)   # game window size; tests that need a close look set a larger one
OFFSCREEN = False  # open the game window off-screen (not minimized) so it can be captured  # save every rendered frame as PNG in the temp user folder
DISABLE_CODES = []  # Slippi Dolphin code names to disable in the temp user folder only
SONIC_CSS_X, SONIC_CSS_Y = -29.0, 4.5  # v76: left end of the bottom row, left of Pichu (v1-v75: 27.2, 4.5, right of Roy)

# libmelee does not know m-ex fighter IDs; map unknown ones instead of crashing and remember them.
UNKNOWN_CHARACTER_IDS = []


def _missing(cls, value):
    UNKNOWN_CHARACTER_IDS.append(value)
    return cls.UNKNOWN_CHARACTER


enums.Character._missing_ = classmethod(_missing)


def other_dolphins():
    out = []
    for p in psutil.process_iter(["pid", "name"]):
        # only Slippi Dolphin creates the slippibot input pipes; a plain Dolphin the user runs does not conflict
        if "slippi dolphin" in (p.info["name"] or "").lower():
            out.append((p.info["pid"], p.info["name"]))
    return out


def pipe_server_pid(port):
    import win32file
    import win32pipe
    try:
        h = win32file.CreateFile(rf"\\.\pipe\slippibot{port}", 0, 0, None, win32file.OPEN_EXISTING, 0, None)
    except Exception as e:
        return f"error: {e}"
    try:
        return win32pipe.GetNamedPipeServerProcessId(h)
    finally:
        win32file.CloseHandle(h)


class Session:
    def __init__(self, iso, log_path):
        self.iso = iso
        self.log_path = log_path
        self.console = None
        self.c1 = self.c2 = None
        self.rows = []

    def start(self, connect_slippi=True):
        running = other_dolphins()
        if running:
            raise SystemExit(f"Another Dolphin is running {running}; close it first.")
        # start minimized, without taking focus
        real_popen = subprocess.Popen

        def set_ini(path, section, key, value):
            text = open(path).read() if os.path.exists(path) else ""
            lines = text.splitlines()
            out, in_sec, done = [], False, False
            for ln in lines:
                if ln.strip().startswith("["):
                    if in_sec and not done:
                        out.append(f"{key} = {value}"); done = True
                    in_sec = ln.strip() == f"[{section}]"
                elif in_sec and ln.split("=")[0].strip() == key:
                    ln = f"{key} = {value}"; done = True
                out.append(ln)
            if not done:
                if not in_sec:
                    out.append(f"[{section}]")
                out.append(f"{key} = {value}")
            open(path, "w").write("\n".join(out) + "\n")

        def quiet_popen(cmd, *a, **kw):
            if OFFSCREEN:
                cfg = os.path.join(self.console._get_dolphin_home_path(), "Config")
                os.makedirs(cfg, exist_ok=True)
                ini = os.path.join(cfg, "Dolphin.ini")
                for k, v in (("RenderToMain", "False"), ("RenderWindowXPos", "60"), ("RenderWindowYPos", "60"),
                             ("RenderWindowWidth", str(WIN[0])), ("RenderWindowHeight", str(WIN[1])), ("RenderWindowAutoSize", "False")):
                    set_ini(ini, "Display", k, v)
                if WIN[0] > 640:
                    for k, v in (("EFBScale", "6"), ("InternalResolution", "3")):
                        set_ini(os.path.join(cfg, "GFX.ini"), "Settings", k, v)
                print("game window kept behind other windows", flush=True)
            if DUMP_FRAMES:
                cfg = os.path.join(self.console._get_dolphin_home_path(), "Config")
                os.makedirs(cfg, exist_ok=True)
                set_ini(os.path.join(cfg, "Dolphin.ini"), "Movie", "DumpFrames", "True")
                set_ini(os.path.join(cfg, "GFX.ini"), "Settings", "DumpFramesAsImages", "True")
                self.dump_dir = os.path.join(self.console._get_dolphin_home_path(), "Dump", "Frames")
                os.makedirs(self.dump_dir, exist_ok=True)
                print("frame dump enabled ->", self.dump_dir, flush=True)
            si = subprocess.STARTUPINFO()
            si.dwFlags |= subprocess.STARTF_USESHOWWINDOW
            si.wShowWindow = 7  # SW_SHOWMINNOACTIVE
            kw["startupinfo"] = si
            return real_popen(cmd, *a, **kw)

        self.console = melee.Console(path=SLIPPI_DIR, slippi_port=SLIPPI_PORT, tmp_home_directory=True,
                                     fullscreen=False, save_replays=False, blocking_input=False,
                                     disable_audio=True, setup_gecko_codes=GECKO, **getattr(self, 'console_kwargs', {}))
        self.c1 = melee.Controller(console=self.console, port=1, type=melee.ControllerType.STANDARD)
        self.c2 = melee.Controller(console=self.console, port=2, type=melee.ControllerType.STANDARD)
        if DISABLE_CODES and not GECKO:
            gs_dir = os.path.join(self.console._get_dolphin_home_path(), "GameSettings")
            os.makedirs(gs_dir, exist_ok=True)
            with open(os.path.join(gs_dir, "GALE01r2.ini"), "w") as f:
                f.write("[Gecko_Disabled]\n" + "\n".join(DISABLE_CODES) + "\n")
            print("temp-only GameSettings: disabled", DISABLE_CODES, flush=True)
        subprocess.Popen = quiet_popen
        try:
            self.console.run(iso_path=self.iso)
        finally:
            subprocess.Popen = real_popen
        self.pid = self.console._process.pid
        if OFFSCREEN:
            self.keep_offscreen()
        print("dolphin pid", self.pid, "temp home", self.console._get_dolphin_home_path(), flush=True)
        if connect_slippi and not self.console.connect():
            raise SystemExit("could not connect to Slippi Dolphin")
        ok1, ok2 = self.c1.connect(), self.c2.connect()
        print("controllers connected:", ok1, ok2, flush=True)
        for port in (1, 2):
            print(f"pipe slippibot{port} server pid:", pipe_server_pid(port), "(test dolphin is", self.pid, ")", flush=True)

    def watchdog(self, shot_path, stall_seconds=12):
        """If no frame arrives for stall_seconds: report, screenshot the Dolphin window, and unblock step()."""
        import threading
        self.last_frame_time = time.time()
        self.stalled = False

        def run():
            while self.console is not None and not self.stalled:
                time.sleep(1)
                if time.time() - self.last_frame_time > stall_seconds:
                    self.stalled = True
                    try:
                        pr = psutil.Process(self.pid)
                        print("STALL: no frames for", stall_seconds, "s | dolphin alive:", pr.is_running(), "status:", pr.status(), "cpu%:", pr.cpu_percent(interval=1.0), flush=True)
                    except Exception as e:
                        print("STALL: dolphin process gone:", e, flush=True)
                    print("STALL last rows:", self.rows[-2:], flush=True)
                    try:
                        self.screenshot(shot_path)
                    except Exception as e:
                        print("screenshot failed:", e, flush=True)
                    self.console.interrupt()
        threading.Thread(target=run, daemon=True).start()

    def keep_offscreen(self):
        """Move this Dolphin's game window off-screen as soon as it exists (no activation, no focus change)."""
        import threading
        import win32con, win32gui, win32process

        def run():
            while self.console is not None and self.console._process is not None and self.console._process.poll() is None:
                def cb(h, _):
                    try:
                        if win32gui.IsWindowVisible(h) and win32process.GetWindowThreadProcessId(h)[1] == self.pid:
                            title = win32gui.GetWindowText(h)
                            if not title.startswith(("Faster Melee", "Warning")):
                                # behind every other window, never activated (a fully off-screen window renders black)
                                if WIN[0] > 640:
                                    win32gui.SetWindowPos(h, win32con.HWND_BOTTOM, 20, 20, WIN[0], WIN[1], win32con.SWP_NOACTIVATE)
                                else:
                                    win32gui.SetWindowPos(h, win32con.HWND_BOTTOM, 0, 0, 0, 0, win32con.SWP_NOSIZE | win32con.SWP_NOMOVE | win32con.SWP_NOACTIVATE)
                    except Exception:
                        pass
                win32gui.EnumWindows(cb, None)
                time.sleep(0.25)
        threading.Thread(target=run, daemon=True).start()

    def capture_game(self, path):
        """Capture the off-screen game window without showing or focusing it."""
        import ctypes
        import win32gui, win32process, win32ui
        from PIL import Image
        try:
            ctypes.windll.shcore.SetProcessDpiAwareness(2)
        except Exception:
            pass
        wins = []

        def cb(h, _):
            if win32gui.IsWindowVisible(h) and win32process.GetWindowThreadProcessId(h)[1] == self.pid:
                l, t, r, b = win32gui.GetWindowRect(h)
                wins.append(((r - l) * (b - t), win32gui.GetWindowText(h), h, (l, t, r, b)))
        win32gui.EnumWindows(cb, None)
        cands = [w for w in wins if not w[1].startswith(("Faster Melee", "Warning"))]
        if not cands:
            return None
        _, title, h, (l, t, r, b) = max(cands)
        w, hh = r - l, b - t
        dc = win32gui.GetWindowDC(h); mdc = win32ui.CreateDCFromHandle(dc); cdc = mdc.CreateCompatibleDC()
        bmp = win32ui.CreateBitmap(); bmp.CreateCompatibleBitmap(mdc, w, hh); cdc.SelectObject(bmp)
        ctypes.windll.user32.PrintWindow(h, cdc.GetSafeHdc(), 2)
        img = Image.frombuffer("RGB", (w, hh), bmp.GetBitmapBits(True), "raw", "BGRX", 0, 1)
        img.save(path)
        win32gui.DeleteObject(bmp.GetHandle()); cdc.DeleteDC(); mdc.DeleteDC(); win32gui.ReleaseDC(h, dc)
        return title, (l, t, r, b)

    def screenshot(self, path):
        import ctypes
        try:
            ctypes.windll.shcore.SetProcessDpiAwareness(2)
        except Exception:
            pass
        import win32gui, win32process, win32ui
        from PIL import Image
        found = []

        def cb(h, _):
            if win32gui.IsWindowVisible(h) and win32process.GetWindowThreadProcessId(h)[1] == self.pid:
                found.append((win32gui.GetWindowText(h), h))
        win32gui.EnumWindows(cb, None)
        print("dolphin windows:", [t for t, _ in found], flush=True)
        for title, h in found:
            texts = []
            win32gui.EnumChildWindows(h, lambda ch, _: texts.append(win32gui.GetWindowText(ch)) or True, None)
            if title == "Warning":
                print("dialog text:", [t for t in texts if t], flush=True)
        for i, (title, h) in enumerate(found):
            win32gui.ShowWindow(h, 4)  # SW_SHOWNOACTIVATE
            time.sleep(0.7)
            l, t, r, b = win32gui.GetWindowRect(h)
            w, hh = r - l, b - t
            if w < 50 or hh < 50:
                continue
            dc = win32gui.GetWindowDC(h); mdc = win32ui.CreateDCFromHandle(dc); cdc = mdc.CreateCompatibleDC()
            bmp = win32ui.CreateBitmap(); bmp.CreateCompatibleBitmap(mdc, w, hh); cdc.SelectObject(bmp)
            ctypes.windll.user32.PrintWindow(h, cdc.GetSafeHdc(), 2)
            img = Image.frombuffer("RGB", (w, hh), bmp.GetBitmapBits(True), "raw", "BGRX", 0, 1)
            out = path.replace(".png", f"_{i}.png"); img.save(out); print("saved", out, "|", title, flush=True)
            win32gui.DeleteObject(bmp.GetHandle()); cdc.DeleteDC(); mdc.DeleteDC(); win32gui.ReleaseDC(h, dc)

    def stop(self):
        if self.console is not None:
            self.console.stop()  # kills only the process this console started
        with open(self.log_path, "w", newline="") as f:
            w = csv.writer(f)
            w.writerow(["frame", "menu", "p1_char", "p1_action", "p1_action_frame", "p1_x", "p1_y", "p1_pct", "p1_stock",
                        "p2_char", "p2_action", "p2_action_frame", "p2_x", "p2_y", "p2_pct", "p2_stock"])
            w.writerows(self.rows)

    def log(self, gs):
        self.last_frame_time = time.time()
        row = [gs.frame, gs.menu_state.name]
        for port in (1, 2):
            p = gs.players.get(port)
            if p is None:
                row += [""] * 7
            else:
                act = p.action.name if hasattr(p.action, "name") else p.action
                row += [p.character.name, act, p.action_frame, round(float(p.position.x), 3), round(float(p.position.y), 3), p.percent, p.stock]
        self.rows.append(row)

    def pick_sonic(self, gs, controller):
        return self.pick_at(gs, controller, SONIC_CSS_X, SONIC_CSS_Y)

    def pick_vanilla(self, gs, controller, character):
        """Pick an original character by icon position (libmelee's own picker misreads IDs under m-ex)."""
        idx = enums.from_internal(character)
        row, col = idx // 9, idx % 9
        if row == 2:
            col += 1
        return self.pick_at(gs, controller, -32.5 + 3.5 + col * 7.0, 1 + 3.5 + (2 - row) * 7.0)

    def pick_at(self, gs, controller, tx, ty):
        """Move the cursor to (tx, ty) on the select screen and press A until a character is locked in."""
        p = gs.players.get(controller.port)
        if p is None:
            controller.release_all()
            return False
        if p.coin_down:
            controller.release_all()
            return True
        x, y = p.cursor.x, p.cursor.y
        controller.release_button(enums.Button.BUTTON_A)
        if y < ty - 1.5:
            controller.tilt_analog(enums.Button.BUTTON_MAIN, .5, 1); return False
        if y > ty + 1.5:
            controller.tilt_analog(enums.Button.BUTTON_MAIN, .5, 0); return False
        if x < tx - 1.5:
            controller.tilt_analog(enums.Button.BUTTON_MAIN, 1, .5); return False
        if x > tx + 1.5:
            controller.tilt_analog(enums.Button.BUTTON_MAIN, 0, .5); return False
        controller.tilt_analog(enums.Button.BUTTON_MAIN, .5, .5)
        if gs.frame % 2 == 0:
            controller.press_button(enums.Button.BUTTON_A)
        return False
