"""Shared by the Wayland backends."""
from dataclasses import dataclass


@dataclass
class Window:
    id: object      # whatever the desktop uses to name a window (number, address, uuid)
    title: str
    width: int
    height: int
