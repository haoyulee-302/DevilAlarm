"""Native DPI rendering and layout scaling, without bitmap magnification."""
import ctypes
import sys
import tkinter as tk
from tkinter import font as tkfont


def enable_high_dpi():
    # Must run before the first Tk window is created.
    # https://learn.microsoft.com/windows/win32/hidpi/setting-the-default-dpi-awareness-for-a-process
    if sys.platform != "win32":
        return
    try:
        set_context = ctypes.windll.user32.SetProcessDpiAwarenessContext
        set_context.argtypes = [ctypes.c_void_p]
        set_context.restype = ctypes.c_bool
        if set_context(ctypes.c_void_p(-4)):
            return
    except (AttributeError, OSError):
        pass
    try:
        ctypes.windll.shcore.SetProcessDpiAwareness(2)
    except (AttributeError, OSError):
        try:
            ctypes.windll.user32.SetProcessDPIAware()
        except (AttributeError, OSError):
            pass


def window_dpi(window):
    if sys.platform == "win32":
        try:
            get_dpi = ctypes.windll.user32.GetDpiForWindow
            get_dpi.argtypes = [ctypes.c_void_p]
            get_dpi.restype = ctypes.c_uint
            dpi = get_dpi(window.winfo_id())
            if dpi:
                return dpi
        except (AttributeError, OSError):
            pass
    return float(window.winfo_fpixels("1i"))


class DisplayScaling:
    def __init__(self, root):
        self.root = root
        self.widgets = []
        self.scale = 1.0
        self.capture(root)

    def capture(self, parent):
        for widget in parent.winfo_children():
            metrics = {}
            for option in ("padx", "pady", "borderwidth", "highlightthickness", "wraplength"):
                if option in widget.keys():
                    metrics[option] = float(str(widget.cget(option)))
            # Text widgets use character units for width/height; leave those alone.
            if isinstance(widget, tk.Scale):
                for option in ("length", "width", "sliderlength"):
                    metrics[option] = float(str(widget.cget(option)))
            if isinstance(widget, tk.Canvas):
                metrics["height"] = float(widget.cget("height"))
            font = None
            if "font" in widget.keys():
                font = tkfont.Font(root=self.root, font=widget.cget("font")).actual()
            manager = widget.winfo_manager()
            geometry = widget.pack_info() if manager == "pack" else widget.grid_info() if manager == "grid" else {}
            gaps = {key: geometry[key] if isinstance(geometry[key], tuple) else self.root.tk.splitlist(str(geometry[key]))
                    for key in ("padx", "pady", "ipadx", "ipady") if key in geometry}
            self.widgets.append((widget, metrics, font, manager, gaps))
            self.capture(widget)

    def apply(self, scale):
        self.scale = scale
        for widget, metrics, font, manager, gaps in self.widgets:
            options = {key: round(value * scale) for key, value in metrics.items()}
            if font:
                size = font["size"]
                pixels = size * 96 / 72 if size > 0 else abs(size)
                options["font"] = (font["family"], -max(1, round(pixels * scale)), font["weight"], font["slant"])
            widget.configure(**options)
            scaled = {key: tuple(round(float(str(value)) * scale) for value in values) for key, values in gaps.items()}
            if manager == "pack":
                widget.pack_configure(**scaled)
            elif manager == "grid":
                widget.grid_configure(**scaled)

