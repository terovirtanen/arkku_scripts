# Generating font10_fi.py for MicroPython Writer

This repository does not vendor `font_to_py.py`. To generate `font10_fi.py` on Windows:

1. Ensure Python 3 is installed and on PATH.
2. Install freetype bindings:
   - `python -m pip install freetype-py`
3. Download Peter Hinch's generator:
   - `Invoke-WebRequest -Uri "https://raw.githubusercontent.com/peterhinch/micropython-font-to-py/master/font_to_py.py" -OutFile "fonts\font_to_py.py"`
4. Generate a 10px font from Arial including Finnish characters:
   - `python fonts\font_to_py.py "C:\Windows\Fonts\arial.ttf" 10 raspberry\infoscreen\font10_fi.py -x --charset_file fonts\charset_fi.txt`

Notes:
- Change the TTF path to any installed font you prefer.
- Use `-f` for monospaced output if you need fixed width.
- Adjust pixel height if 10px is too small for your display.
- The output module exposes the Writer API (`height()`, `get_ch()`, etc.).
