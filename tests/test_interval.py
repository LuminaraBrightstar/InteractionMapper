import unittest
import tkinter as tk
import autoclicker

class TestInterval(unittest.TestCase):
    def test_min_interval_enforced(self):
        root = tk.Tk()
        try:
            app = autoclicker.AutoClicker(root, interval=0)
            self.assertEqual(app.get_interval(), 0.001)
        finally:
            root.destroy()

if __name__ == '__main__':
    unittest.main()
