import tkinter as tk
import threading
import time
try:
    import pyautogui
except ImportError:
    raise SystemExit('pyautogui is required. Install with `pip install pyautogui`.')
try:
    import keyboard
except ImportError:
    raise SystemExit('keyboard is required. Install with `pip install keyboard`.')

class AutoClicker:
    def __init__(self, master):
        self.master = master
        master.title("Simple Auto Clicker")

        self.interval_var = tk.DoubleVar(value=1.0)
        self.hotkey_var = tk.StringVar(value="F8")

        tk.Label(master, text="Interval (seconds):").grid(row=0, column=0, padx=5, pady=5)
        self.interval_entry = tk.Entry(master, textvariable=self.interval_var)
        self.interval_entry.grid(row=0, column=1, padx=5, pady=5)

        tk.Label(master, text="Hotkey:").grid(row=1, column=0, padx=5, pady=5)
        self.hotkey_entry = tk.Entry(master, textvariable=self.hotkey_var)
        self.hotkey_entry.grid(row=1, column=1, padx=5, pady=5)
        self.set_hotkey_button = tk.Button(master, text="Set Hotkey", command=self.register_hotkey)
        self.set_hotkey_button.grid(row=1, column=2, padx=5, pady=5)

        self.start_button = tk.Button(master, text="Start", command=self.start_clicking)
        self.start_button.grid(row=2, column=0, padx=5, pady=5)

        self.stop_button = tk.Button(master, text="Stop", command=self.stop_clicking, state=tk.DISABLED)
        self.stop_button.grid(row=2, column=1, padx=5, pady=5)

        self.clicking = False
        self.thread = None
        self.hotkey_handle = None
        self.register_hotkey()

    def click_loop(self):
        while self.clicking:
            pyautogui.click()
            time.sleep(max(self.interval_var.get(), 0.001))

    def register_hotkey(self):
        hk = self.hotkey_var.get().strip()
        if self.hotkey_handle is not None:
            keyboard.remove_hotkey(self.hotkey_handle)
        self.hotkey_handle = keyboard.add_hotkey(hk, self.toggle_clicking)

    def toggle_clicking(self):
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

if __name__ == "__main__":
    root = tk.Tk()
    app = AutoClicker(root)
    root.mainloop()
