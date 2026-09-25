# Screen Preview Tool
 
Live preview window for one of your monitors, with dropdowns to pick which
monitor to preview and to move any open window onto a chosen monitor.
Useful when a monitor is set to "Extend" and you can't see it directly
(e.g. a GM running a secondary display for players).
 
## Requirements
 
- Python 3.11+
- Dependencies: See [requirements.txt](https://github.com/Ookean/screen-previewer/blob/main/requirements.txt)
## Quick install (regular pip installer)
 
If you just want to run the tool:
 
```
pip install mss pillow pygetwindow pywin32
python screen_preview.py
```
 
## Development setup (venv)
 
This project is developed inside a virtual environment to keep dependencies isolated:
 
```
python -m venv venv
venv\Scripts\activate      # Windows
source venv/bin/activate   # macOS/Linux
pip install mss pillow pygetwindow pywin32
python screen_preview.py
```
 
## Usage
 
```
python screen_preview.py             # open the app
python screen_preview.py --monitor 2 # preselect a monitor at launch
python screen_preview.py --list      # list monitors and exit
```
 
## License
 
Open source — free to use, modify, and share. See the
[MIT License](https://opensource.org/license/mit/) for terms.

