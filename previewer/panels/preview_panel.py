"""Feature: the live preview of the selected monitor."""
import tkinter as tk

from PIL import Image, ImageTk

from ..i18n import t


class PreviewPanel(tk.Label):
    REFRESH_MS = 100  # ~10 fps

    def __init__(self, parent, model):
        super().__init__(parent, bg="black", fg="white", wraplength=500)
        self.model = model
        self._tk_img = None      # keep a reference, or Tk drops the image
        self._after_id = None

    def start(self):
        self._update()

    def destroy(self):
        # Stop the refresh loop, or it would keep running against a destroyed widget.
        if self._after_id is not None:
            self.after_cancel(self._after_id)
            self._after_id = None
        super().destroy()

    def _update(self):
        try:
            monitor = self.model.current
            img = None if monitor is None else self.model.capture.grab(monitor)
            if img is not None:
                w, h = self.winfo_width(), self.winfo_height()
                if w > 1 and h > 1:
                    img_ratio = img.width / img.height
                    if w / h > img_ratio:
                        new_h, new_w = h, int(h * img_ratio)
                    else:
                        new_w, new_h = w, int(w / img_ratio)
                    img = img.resize((max(1, new_w), max(1, new_h)), Image.BILINEAR)

                self._tk_img = ImageTk.PhotoImage(img)
                self.configure(image=self._tk_img, text="")
            else:
                status = self.model.capture.status()   # e.g. Wayland: waiting for the permission dialog
                if status:
                    self._tk_img = None
                    self.configure(image="", text=t(status[0], **status[1]))
        except Exception as e:
            print(f"Preview error: {e}")

        self._after_id = self.after(self.REFRESH_MS, self._update)
