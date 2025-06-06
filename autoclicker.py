import tkinter as tk
import threading
import time
import ctypes
try:
    import pyautogui
except ImportError:
    raise SystemExit('pyautogui is required. Install with `pip install pyautogui`.')
try:
    from pynput import keyboard
except ImportError:
    raise SystemExit('pynput is required. Install with `pip install pynput`.')

SendInput = ctypes.windll.user32.SendInput

class MouseInput(ctypes.Structure):
    _fields_ = [("dx", ctypes.c_long),
                ("dy", ctypes.c_long),
                ("mouseData", ctypes.c_ulong),
                ("dwFlags", ctypes.c_ulong),
                ("time", ctypes.c_ulong),
                ("dwExtraInfo", ctypes.POINTER(ctypes.c_ulong))]

class Input_I(ctypes.Union):
    _fields_ = [("mi", MouseInput)]

class Input(ctypes.Structure):
    _fields_ = [("type", ctypes.c_ulong),
                ("ii", Input_I)]

def click_fast():
    MOUSEEVENTF_LEFTDOWN = 0x0002
    MOUSEEVENTF_LEFTUP = 0x0004
    extra = ctypes.c_ulong(0)
    ii_ = Input_I()
    ii_.mi = MouseInput(0, 0, 0, MOUSEEVENTF_LEFTDOWN, 0, ctypes.pointer(extra))
    command = Input(ctypes.c_ulong(0), ii_)
    SendInput(1, ctypes.pointer(command), ctypes.sizeof(command))
    ii_.mi = MouseInput(0, 0, 0, MOUSEEVENTF_LEFTUP, 0, ctypes.pointer(extra))
    command = Input(ctypes.c_ulong(0), ii_)
    SendInput(1, ctypes.pointer(command), ctypes.sizeof(command))

class AutoClicker:
    def __init__(self, master):
        self.master = master
        master.title("Simple Auto Clicker")

        self.interval_var = tk.DoubleVar(value=1.0)
        self.benchmark_var = tk.BooleanVar(value=False)
        self.hotkey_var = tk.StringVar(value="F6")

        tk.Label(master, text="Interval (seconds):").grid(row=0, column=0, padx=5, pady=5)
        self.interval_entry = tk.Entry(master, textvariable=self.interval_var)
        self.interval_entry.grid(row=0, column=1, padx=5, pady=5)

        tk.Checkbutton(master, text="Benchmark Mode (Max Speed)", variable=self.benchmark_var).grid(row=1, column=0, columnspan=2, pady=5)

        tk.Label(master, text="Hotkey:").grid(row=2, column=0, padx=5, pady=5)
        self.hotkey_entry = tk.Entry(master, textvariable=self.hotkey_var)
        self.hotkey_entry.grid(row=2, column=1, padx=5, pady=5)
        self.hotkey_entry.bind("<Key>", self.on_hotkey_press)

        self.start_button = tk.Button(master, text="Start", command=self.start_clicking)
        self.start_button.grid(row=3, column=0, padx=5, pady=5)

        self.stop_button = tk.Button(master, text="Stop", command=self.stop_clicking, state=tk.DISABLED)
        self.stop_button.grid(row=3, column=1, padx=5, pady=5)

        self.clicking = False
        self.thread = None
        self.listener = None

        self.hotkey_var.trace_add("write", lambda *args: self.setup_hotkey_listener())
        self.setup_hotkey_listener()

        master.bind_all("<Button-1>", self.unfocus_hotkey, add="+")

    def on_hotkey_press(self, event):
        key = event.keysym
        if len(key) == 1 and not key.isalnum():
            return "break"
        self.hotkey_var.set(key.upper())
        return "break"

    def unfocus_hotkey(self, event):
        if event.widget != self.hotkey_entry and not isinstance(event.widget, tk.Entry):
            self.hotkey_entry.selection_clear()
            self.master.focus_set()

    def click_loop(self):
        if self.benchmark_var.get():
            while self.clicking:
                click_fast()
        else:
            interval = self.interval_var.get()
            if interval < 0.001:
                interval = 0.001
                self.interval_var.set(0.001)
            next_time = time.perf_counter()
            while self.clicking:
                now = time.perf_counter()
                if now >= next_time:
                    click_fast()
                    next_time += interval
                time.sleep(0.0005)

    def setup_hotkey_listener(self):
        hotkey = self.hotkey_var.get().strip()
        if not hotkey:
            return
        if self.listener:
            self.listener.stop()
            self.listener = None
        normalized = f"<{hotkey.lower()}>"
        self.listener = keyboard.GlobalHotKeys({normalized: self.toggle_clicking})
        self.listener.start()

    def toggle_clicking(self):
        self.master.after(0, self._toggle_clicking)

    def _toggle_clicking(self):
        if self.clicking:
            self.stop_clicking()
        else:
            self.start_clicking()

    def start_clicking(self):
        if not self.clicking:
            self.clicking = True
            self.start_button.config(state=tk.DISABLED)
            self.stop_button.config(state=tk.NORMAL)
            self.thread = threading.Thread(target=self.click_loop, daemon=True)
            self.thread.start()

    def stop_clicking(self):
        if self.clicking:
            self.clicking = False
            self.start_button.config(state=tk.NORMAL)
            self.stop_button.config(state=tk.DISABLED)

    def on_close(self):
        if self.listener:
            self.listener.stop()
            self.listener = None
        self.master.destroy()

if __name__ == "__main__":
    root = tk.Tk()
    app = AutoClicker(root)
    root.protocol("WM_DELETE_WINDOW", app.on_close)
    root.mainloop()
