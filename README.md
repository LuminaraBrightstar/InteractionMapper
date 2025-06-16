# InteractionMapper

A lightweight cross-platform auto clicker written in Python.

## Requirements
- Python 3.x
- Dependencies listed in `requirements.txt`

Install them with:

```bash
pip install -r requirements.txt
```

## Usage
Run the autoclicker:

```bash
python autoclicker.py [--interval SECONDS] [--hotkey KEY] [--benchmark]
```

A window will open allowing you to change the click interval and hotkey. The
`--benchmark` flag or the checkbox in the UI enables maximum speed clicking.
You can press the Start/Stop buttons or the selected hotkey (default `F6`) to
toggle the clicker.

On Windows, the clicker uses the fast native `SendInput` API. Other platforms
fall back to `pyautogui`. Benchmark mode may not reach the same speed on
non-Windows systems.
