"""Window layouts: pure geometry, shared by every platform."""
from dataclasses import dataclass
from typing import Optional

# Layout ids. The UI shows a translated label for each ("layout.<id>" in the locale files).
LAYOUTS = ["center", "maximize", "left_half", "right_half", "top_half", "bottom_half"]


@dataclass
class Placement:
    x: int
    y: int
    width: Optional[int] = None    # None = keep the window's current size
    height: Optional[int] = None
    maximize: bool = False


def compute_placement(monitor, layout, win_width, win_height):
    """Where a window of the given size should go on `monitor` for the layout id `layout`."""
    left, top = monitor["left"], monitor["top"]
    width, height = monitor["width"], monitor["height"]

    if layout == "left_half":
        return Placement(left, top, width // 2, height)
    if layout == "right_half":
        return Placement(left + width // 2, top, width - width // 2, height)
    if layout == "top_half":
        return Placement(left, top, width, height // 2)
    if layout == "bottom_half":
        return Placement(left, top + height // 2, width, height - height // 2)

    # "center" and "maximize": move first, so a maximize happens on the target monitor.
    x = left + max(0, (width - win_width) // 2)
    y = top + max(0, (height - win_height) // 2)
    return Placement(x, y, maximize=(layout == "maximize"))
