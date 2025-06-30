#!/usr/bin/env python3
import sys
import argparse
import ctypes
import logging
import threading
import time
import tkinter as tk

# —— platform-specific click implementation —— #
try:
    import pyautogui
    pyautogui.FAILSAFE = False
except ImportError:
    pyautogui = None

if sys.platform == "win32" and ctypes:
    SendInput = ctypes.windll.user32.SendInput

    class _MouseInput(ctypes.Structure):
        _fields_ = [
            ("dx", ctypes.c_long),
            ("dy", ctypes.c_long),
            ("mouseData", ctypes.c_ulong),
            ("dwFlags", ctypes.c_ulong),
            ("time", ctypes.c_ulong),
            ("dwExtraInfo", ctypes.POINTER(ctypes.c_ulong)),
        ]

    class _InputI(ctypes.Union):
        _fields_ = [("mi", _MouseInput)]

    class _Input(ctypes.Structure):
        _fields_ = [("type", ctypes.c_ulong), ("ii", _InputI)]

    def click_fast() -> None:
        """Windows high-speed click via SendInput."""
        MOUSEEVENTF_DOWN = 0x0002
        MOUSEEVENTF_UP   = 0x0004
        extra = ctypes.c_ulong(0)
        ii = _InputI()
        # down
        ii.mi = _MouseInput(0, 0, 0, MOUSEEVENTF_DOWN, 0, ctypes.pointer(extra))
        cmd = _Input(ctypes.c_ulong(0), ii)
        SendInput(1, ctypes.pointer(cmd), ctypes.sizeof(cmd))
        # up
        ii.mi = _MouseInput(0, 0, 0, MOUSEEVENTF_UP, 0, ctypes.pointer(extra))
        cmd = _Input(ctypes.c_ulong(0), ii)
        SendInput(1, ctypes.pointer(cmd), ctypes.sizeof(cmd))

elif pyautogui:
    def click_fast() -> None:
        """Fallback click via pyautogui."""
        pyautogui.click()
else:
    raise SystemExit("Either Windows ctypes or pyautogui is required.")

# —— core clicking logic —— #
class ClickerController:
    def __init__(self, interval: float = 1.0, benchmark: bool = False):
        self.interval = max(0.001, interval)
        self.benchmark = benchmark
        self._clicking = False
        self._thread = None
        self._callbacks = []

    def register_callback(self, fn):
        """Register a callback to run after each click."""
        self._callbacks.append(fn)

    def _run_loop(self):
        logging.info("Click loop started (benchmark=%s)", self.benchmark)
        next_t = time.perf_counter()
        while self._clicking:
            now = time.perf_counter()
            if self.benchmark or now >= next_t:
                click_fast()
                for cb in self._callbacks:
                    try:
                        cb()
                    except Exception:
                        pass
                next_t += self.interval
            time.sleep(0.0005)
        logging.info("Click loop stopped")

    def start(self):
        if not self._clicking:
            self._clicking = True
            self._thread = threading.Thread(target=self._run_loop, daemon=True)
            self._thread.start()

    def stop(self):
        self._clicking = False

    def toggle(self):
        """Toggle between start and stop."""
        if self._clicking:
            self.stop()
        else:
            self.start()

    def set_interval(self, val: float):
        self.interval = max(0.001, val)

    def set_benchmark(self, on: bool):
        self.benchmark = bool(on)

# —— hotkey management —— #
try:
    from pynput import keyboard
except ImportError:
    raise SystemExit('pynput is required. Install with `pip install pynput`.')

class HotkeyManager:
    def __init__(self, hotkey: str, callback):
        """
        hotkey: e.g. 'F6', 'a', etc.
        callback: function to call on key press.
        """
        self._hotkey = hotkey.lower()
        self._callback = callback
        self._listener = None
        self._start_listener()

    def _norm(self, key: str) -> str:
        return f"<{key.lower()}>"

    def _start_listener(self):
        if self._listener:
            self._listener.stop()
        key = self._norm(self._hotkey)
        try:
            self._listener = keyboard.GlobalHotKeys({key: self._callback})
            self._listener.start()
            logging.info("Registered hotkey %s", self._hotkey)
        except Exception as e:
            logging.error("Hotkey registration failed for %s: %s", self._hotkey, e)

    def change(self, new_hotkey: str):
        self._hotkey = new_hotkey
        self._start_listener()

    def stop(self):
        if self._listener:
            self._listener.stop()
            self._listener = None

# —— GUI layer —— #
class AutoClickerGUI:
    def __init__(self, controller: ClickerController, hotkey_mgr: HotkeyManager):
        self.ctrl = controller
        self.hk   = hotkey_mgr

        self.root = tk.Tk()
        self.root.title("AutoClicker")

        self.interval_var  = tk.DoubleVar(value=self.ctrl.interval)
        self.benchmark_var = tk.BooleanVar(value=self.ctrl.benchmark)
        self.hotkey_var    = tk.StringVar(value=self.hk._hotkey.upper())
        self.click_count   = tk.IntVar(value=0)

        # Layout
        tk.Label(self.root, text="Interval (s):").grid(row=0, column=0, padx=5, pady=5)
        tk.Entry(self.root, textvariable=self.interval_var).grid(row=0, column=1, padx=5, pady=5)

        tk.Checkbutton(self.root, text="Benchmark Mode", variable=self.benchmark_var)\
            .grid(row=1, column=0, columnspan=2, pady=5)

        tk.Label(self.root, text="Hotkey:").grid(row=2, column=0, padx=5, pady=5)
        hk_entry = tk.Entry(self.root, textvariable=self.hotkey_var)
        hk_entry.grid(row=2, column=1, padx=5, pady=5)
        hk_entry.bind("<FocusOut>", self._on_hotkey_change)

        tk.Button(self.root, text="Start", command=self._on_start)\
            .grid(row=3, column=0, padx=5, pady=5)
        tk.Button(self.root, text="Stop",  command=self._on_stop)\
            .grid(row=3, column=1, padx=5, pady=5)

        tk.Label(self.root, text="Clicks:").grid(row=4, column=0, padx=5, pady=5)
        tk.Label(self.root, textvariable=self.click_count).grid(row=4, column=1, padx=5, pady=5)

        # callback to update count
        self.ctrl.register_callback(lambda: self.root.after(0, self.click_count.set, self.click_count.get()+1))

        self.root.protocol("WM_DELETE_WINDOW", self._on_close)

    def _on_start(self):
        self.ctrl.set_interval(self.interval_var.get())
        self.ctrl.set_benchmark(self.benchmark_var.get())
        self.ctrl.start()

    def _on_stop(self):
        self.ctrl.stop()

    def _on_hotkey_change(self, event):
        new = self.hotkey_var.get().strip()
        if new:
            self.hk.change(new)

    def _on_close(self):
        self.hk.stop()
        self.ctrl.stop()
        self.root.destroy()

    def run(self):
        self.root.mainloop()

# —— entry point —— #
def main():
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
    parser = argparse.ArgumentParser(description="Modular single-file AutoClicker")
    parser.add_argument("--interval", type=float, default=1.0, help="click interval in seconds")
    parser.add_argument("--benchmark", action="store_true", help="disable timing limit")
    parser.add_argument("--hotkey", type=str, default="F6", help="toggle hotkey")
    args = parser.parse_args()

    ctrl = ClickerController(interval=args.interval, benchmark=args.benchmark)
    hk   = HotkeyManager(args.hotkey, ctrl.toggle)
    gui  = AutoClickerGUI(ctrl, hk)
    gui.run()

if __name__ == "__main__":
    main()

 # —— new keyboard‐auto‐press controller —— #
import pynput.keyboard as _kb

class KeyboardController:
    def __init__(self, key: str = 'a', interval: float = 1.0):
        self.key       = key
        self.interval  = max(0.001, interval)
        self._pressing = False
        self._thread   = None
        self._kbd      = _kb.Controller()

    def _press(self):
        # press & release once
        self._kbd.press(self.key)
        self._kbd.release(self.key)

    def _loop(self):
        next_t = time.perf_counter()
        while self._pressing:
            now = time.perf_counter()
            if now >= next_t:
                self._press()
                next_t += self.interval
            time.sleep(0.0005)

    def start(self):
        if not self._pressing:
            self._pressing = True
            self._thread   = threading.Thread(target=self._loop, daemon=True)
            self._thread.start()

    def stop(self):
        self._pressing = False

    def toggle(self):
        if self._pressing:
            self.stop()
        else:
            self.start()

 # —— entry point —— #
def main():
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
    parser = argparse.ArgumentParser(description="Modular single-file AutoClicker")
    # existing args:
    parser.add_argument("--interval", type=float, default=1.0, help="click interval")
    parser.add_argument("--hotkey",   type=str,   default="F6", help="click toggle key")
    # new args for keyboard auto-press:
    parser.add_argument("--key",         type=str,   default="a",   help="which key to auto-press")
    parser.add_argument("--key-interval",type=float, default=1.0,   help="keyboard interval")
    parser.add_argument("--key-hotkey",  type=str,   default="F7",  help="keyboard toggle key")
    args = parser.parse_args()

    # your existing setup:
    ctrl = ClickerController(interval=args.interval, benchmark=args.benchmark)
    hk   = HotkeyManager(args.hotkey, ctrl.toggle)
    gui  = AutoClickerGUI(ctrl, hk)

    # new keyboard‐press setup:
    kb   = KeyboardController(key=args.key, interval=args.key_interval)
    khk  = HotkeyManager(args.key_hotkey, kb.toggle)

    gui.run()