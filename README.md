# Screen Preview Tool
 
Live preview window for one of your monitors, with dropdowns to pick which
monitor to preview and to move any open window onto a chosen monitor.
Useful when a monitor is set to "Extend" and you can't see it directly
(e.g. a GM running a secondary display for players).
 
## Requirements
 
- Python 3.8+
- Dependencies: `mss`, `pillow`, `pygetwindow`, `pywin32`
  (`pygetwindow`/`pywin32` are only needed for the window-moving feature, Windows-only)
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
 

# Code Signing Policy
 
Free code signing for Windows builds of Screen Preview Tool is provided by
[SignPath.io](https://signpath.io), certificate by [SignPath Foundation](https://signpath.org).
 

To verify authenticity: right-click the downloaded `.exe` → **Properties** →
**Digital Signatures** tab. The signer should be **"SignPath Foundation"**.
 
## Build integrity
 
Signing requests are submitted directly from the CI build of the public
source repository. SignPath verifies the artifact was built from that
repository before applying the signature — the private signing key never
touches this project's build machine.
 
