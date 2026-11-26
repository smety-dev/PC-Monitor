"""Reusable dark dashboard widgets for PC Monitor."""
import tkinter as tk
from tkinter import ttk

BG = "#0b101b"
PANEL = "#141d2d"
SIDEBAR = "#101827"
BORDER = "#243249"
HOVER = "#263951"
SELECTED = "#203e60"
TRACK = "#29384d"
TEXT = "#edf3ff"
MUTED = "#a0b1c9"
BLUE = "#60a5fa"
ORANGE = "#f7ba65"
GREEN = "#46d9b0"
FONT = "Segoe UI"


def label(parent, text="", size=11, color=TEXT, bold=False, bg=PANEL, **kwargs):
    return tk.Label(parent, text=text, font=(FONT, size, "bold" if bold else "normal"),
                    fg=color, bg=bg, **kwargs)


def card(parent):
    return tk.Frame(parent, bg=PANEL, highlightbackground=BORDER, highlightthickness=1)


class Gauge(tk.Frame):
    """Compact metric card with a custom arc and a prominent numeric value."""
    def __init__(self, parent, name, color):
        super().__init__(parent, bg=PANEL, highlightbackground=BORDER, highlightthickness=1)
        self.color = color
        top = tk.Frame(self, bg=PANEL)
        top.pack(fill="x", padx=16, pady=(14, 0))
        label(top, name, 11, MUTED, True).pack(side="left")
        label(top, "●", 11, color).pack(side="right")
        self.canvas = tk.Canvas(self, width=150, height=104, bg=PANEL, highlightthickness=0)
        self.canvas.pack(fill="x", expand=True, padx=8)
        self.value = None
        self.canvas.bind("<Configure>", self.draw)
        self.caption = label(self, "", 9, MUTED)
        self.caption.pack(anchor="w", padx=16, pady=(0, 14))

    def update_value(self, value, caption=""):
        self.value = value
        self.caption.configure(text=caption)
        self.draw()

    def draw(self, event=None):
        c = self.canvas
        c.delete("all")
        w, h = c.winfo_width(), c.winfo_height()
        if w < 50 or h < 40:
            return
        x, y = w/2, h/2 + 8
        r = min(w/2 - 12, h/2 - 8)
        bounds = (x-r, y-r, x+r, y+r)
        c.create_arc(*bounds, start=210, extent=-240, style="arc", outline=TRACK, width=8)
        if self.value is not None:
            value = max(0, min(100, self.value))
            if value > 0:
                c.create_arc(*bounds, start=210, extent=-2.4*value, style="arc", outline=self.color, width=8)
        text = "N/A" if self.value is None else f"{self.value:.1f}%"
        c.create_text(x, y-1, text=text, fill=TEXT, font=(FONT, 19, "bold"))


def action(parent, text, command, primary=True):
    bg = BLUE if primary else TRACK
    fg = BG if primary else TEXT
    return tk.Button(parent, text=text, command=command, bg=bg, fg=fg,
                     activebackground="#91bfff" if primary else HOVER,
                     activeforeground=fg, disabledforeground=MUTED,
                     relief="flat", bd=0, highlightthickness=0,
                     cursor="hand2", font=(FONT, 11, "bold"), padx=14, pady=7)


def table_style(parent, name):
    style = ttk.Style(parent)
    style.configure(name, background=PANEL, fieldbackground=PANEL,
                    foreground=TEXT, rowheight=30, borderwidth=0, font=(FONT, 10))
    style.configure(name + ".Heading", background=TRACK, foreground=MUTED,
                    font=(FONT, 10, "bold"), relief="flat", padding=8)
    style.map(name + ".Heading", background=[("pressed", SELECTED), ("active", HOVER)],
              foreground=[("pressed", TEXT), ("active", TEXT)])
    style.map(name, background=[("selected", SELECTED)], foreground=[("selected", TEXT)])


def stripe_table(table):
    table.tag_configure("even", background=PANEL)
    table.tag_configure("odd", background="#182438")


def chart_style(ax):
    ax.set_facecolor(PANEL)
    ax.tick_params(colors=MUTED, labelsize=9, length=0, pad=7)
    ax.set_axisbelow(True)
    ax.grid(axis="y", color=TRACK, alpha=.8, linewidth=.7)
    for spine in ax.spines.values():
        spine.set_visible(False)


def configure_style(root):
    style = ttk.Style(root)
    style.theme_use("clam")
    style.configure("Dashboard.Horizontal.TProgressbar", troughcolor=TRACK,
                    background=BLUE, bordercolor=PANEL, lightcolor=BLUE,
                    darkcolor=BLUE, thickness=8)
    style.configure("Vertical.TScrollbar", background=TRACK, troughcolor=BG,
                    bordercolor=BG, lightcolor=TRACK, darkcolor=TRACK, arrowcolor=MUTED, width=10)
    style.configure("Dark.Vertical.TScrollbar", background=TRACK, troughcolor=BG,
                    bordercolor=BG, lightcolor=TRACK, darkcolor=TRACK, arrowcolor=MUTED, width=10)
    style.map("Dark.Vertical.TScrollbar", background=[("active", HOVER), ("pressed", SELECTED)])
    style.configure("TCombobox", fieldbackground=PANEL, background=TRACK, foreground=TEXT,
                    arrowcolor=TEXT, bordercolor=BORDER, padding=6)
    style.map("TCombobox", fieldbackground=[("readonly", PANEL), ("disabled", TRACK)],
              foreground=[("readonly", TEXT), ("disabled", MUTED)],
              selectbackground=[("readonly", PANEL)], selectforeground=[("readonly", TEXT)])
    root.option_add("*TCombobox*Listbox.background", PANEL)
    root.option_add("*TCombobox*Listbox.foreground", TEXT)
    root.option_add("*TCombobox*Listbox.selectBackground", SELECTED)
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
