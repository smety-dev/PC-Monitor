"""Reusable dark dashboard widgets for PC Monitor."""
import tkinter as tk
from tkinter import ttk

BG = "#0d1117"
PANEL = "#161e2a"
TRACK = "#303b4b"
TEXT = "#e6edf3"
MUTED = "#94a3b8"
BLUE = "#60a5fa"
ORANGE = "#f59e0b"
GREEN = "#4ade80"
FONT = "Segoe UI"


def label(parent, text="", size=11, color=TEXT, bold=False, bg=PANEL, **kwargs):
    return tk.Label(parent, text=text, font=(FONT, size, "bold" if bold else "normal"),
                    fg=color, bg=bg, **kwargs)


def card(parent):
    return tk.Frame(parent, bg=PANEL, highlightbackground=TRACK, highlightthickness=1)


class Gauge(tk.Frame):
    def __init__(self, parent, name, color):
        super().__init__(parent, bg=PANEL, highlightbackground=TRACK, highlightthickness=1)
        self.color = color
        label(self, name, 11, MUTED, True).pack(pady=(9, 0))
        self.canvas = tk.Canvas(self, width=150, height=132, bg=PANEL,
                                highlightthickness=0)
        self.canvas.pack(fill="x", expand=True)
        self.value = None
        self.canvas.bind("<Configure>", self.draw)
        self.caption = label(self, "", 9, MUTED)
        self.caption.pack(pady=(0, 9))

    def update_value(self, value, caption=""):
        self.value = value
        self.caption.configure(text=caption)
        self.draw()

    def draw(self, event=None):
        c = self.canvas
        c.delete("all")
        w, h = c.winfo_width(), c.winfo_height()
        if w < 20 or h < 20:
            return
        radius = min(w, h) / 2 - 12
        x, y = w / 2, h / 2
        bounds = (x-radius, y-radius, x+radius, y+radius)
        c.create_oval(*bounds, outline=TRACK, width=9)
        if self.value is not None:
            value = max(0, min(100, self.value))
            if value >= 100:
                c.create_oval(*bounds, outline=self.color, width=9)
            elif value > 0:
                c.create_arc(*bounds, start=90, extent=-value*3.6,
                             style="arc", outline=self.color, width=9)
        text = "N/A" if self.value is None else f"{self.value:.1f}%"
        c.create_text(x, y, text=text, fill=self.color, font=(FONT, 18, "bold"))


def configure_style(root):
    style = ttk.Style(root)
    style.theme_use("clam")
    style.configure("Dashboard.TProgressbar", troughcolor=TRACK,
                    background=BLUE, bordercolor=PANEL, lightcolor=BLUE,
                    darkcolor=BLUE, thickness=8)
    style.configure("Dark.Vertical.TScrollbar", background=TRACK,
                    troughcolor=BG, bordercolor=BG, arrowcolor=TEXT)
    return style


class ScrollPage(tk.Frame):
    """Scrollable details page; content width follows the viewport."""
    def __init__(self, parent):
        super().__init__(parent, bg=BG)
        self.canvas = tk.Canvas(self, bg=BG, highlightthickness=0)
        scrollbar = ttk.Scrollbar(self, orient="vertical",
                                  command=self.canvas.yview,
                                  style="Dark.Vertical.TScrollbar")
        self.canvas.configure(yscrollcommand=scrollbar.set)
        scrollbar.pack(side="right", fill="y")
        self.canvas.pack(side="left", fill="both", expand=True)
        self.body = tk.Frame(self.canvas, bg=BG)
        self.window = self.canvas.create_window(0, 0, window=self.body, anchor="nw")
        self.body.bind("<Configure>", lambda e: self.canvas.configure(
            scrollregion=self.canvas.bbox("all")))
        self.canvas.bind("<Configure>", lambda e: self.canvas.itemconfigure(
            self.window, width=e.width))
