import tkinter as tk
import threading
import time
try:
    import pyautogui
except ImportError:
    raise SystemExit('pyautogui is required. Install with `pip install pyautogui`.')
try:
    from pynput import keyboard
except ImportError:
    raise SystemExit('pynput is required. Install with `pip install pynput`.')

class AutoClicker:
    def __init__(self, master):
        self.master = master
        master.title("Simple Auto Clicker")

        self.interval_var = tk.DoubleVar(value=1.0)
        self.hotkey_var = tk.StringVar(value="F6")

        tk.Label(master, text="Interval (seconds):").grid(row=0, column=0, padx=5, pady=5)
        self.interval_entry = tk.Entry(master, textvariable=self.interval_var)
        self.interval_entry.grid(row=0, column=1, padx=5, pady=5)

        tk.Label(master, text="Hotkey:").grid(row=1, column=0, padx=5, pady=5)
        self.hotkey_entry = tk.Entry(master, textvariable=self.hotkey_var)
        self.hotkey_entry.grid(row=1, column=1, padx=5, pady=5)
        self.hotkey_entry.bind("<Key>", self.on_hotkey_press)

        self.start_button = tk.Button(master, text="Start", command=self.start_clicking)
        self.start_button.grid(row=2, column=0, padx=5, pady=5)

        self.stop_button = tk.Button(master, text="Stop", command=self.stop_clicking, state=tk.DISABLED)
        self.stop_button.grid(row=2, column=1, padx=5, pady=5)

        self.clicking = False
        self.thread = None
        self.listener = None

        self.hotkey_var.trace_add("write", lambda *args: self.setup_hotkey_listener())
        self.setup_hotkey_listener()

    def on_hotkey_press(self, event):
        """Capture a single key press in the hotkey entry."""
        key = event.keysym
        # Ignore modifier keys
        if len(key) == 1 and not key.isalnum():
            return "break"
        self.hotkey_var.set(key.upper())
        return "break"

    def click_loop(self):
        while self.clicking:
            pyautogui.click()
            time.sleep(max(self.interval_var.get(), 0.001))

    def setup_hotkey_listener(self):
        hotkey = self.hotkey_var.get().strip()
        if not hotkey:
            return
        if self.listener:
            self.listener.stop()
            self.listener = None
        # Normalize hotkey (e.g., F6 -> <f6>)
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
