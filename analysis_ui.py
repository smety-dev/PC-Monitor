"""Analysis page for PC Monitor CSV recordings."""
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor
from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from dashboard_ui import BG, PANEL, TRACK, TEXT, MUTED, BLUE, ORANGE, GREEN, FONT, ScrollPage, card, label
from performance_analysis import read_recording, summarize, utilization_hints

GROUPS = {
    "Vytížení (%)": (("cpu_percent", "CPU", BLUE), ("ram_percent", "RAM", ORANGE),
                     ("gpu_3d_percent", "GPU 3D", GREEN)),
    "Disky (MiB/s)": (("disk_read_mib_s", "Čtení", BLUE), ("disk_write_mib_s", "Zápis", ORANGE)),
    "Síť (MiB/s)": (("net_receive_mib_s", "Příjem", BLUE), ("net_send_mib_s", "Odesílání", GREEN)),
    "Frekvence (MHz)": (("cpu_frequency_mhz", "CPU", BLUE),),
    "Dostupná RAM (MiB)": (("ram_available_mib", "RAM", ORANGE),),
}


def load_analysis(path):
    rows, skipped = read_recording(path)
    stats = summarize(rows)
    return rows, skipped, stats, utilization_hints(rows, stats)


class AnalysisPage(ScrollPage):
    def __init__(self, parent):
        super().__init__(parent)
        self.rows = []
        self.executor = ThreadPoolExecutor(max_workers=1)
        self.future = None
        self.poll_id = None
        self.closed = False
        toolbar = tk.Frame(self.body, bg=BG)
        toolbar.pack(fill="x", pady=(0, 8))
        self.open_button = tk.Button(toolbar, text="Načíst CSV", command=self.open_file,
                                     bg=BLUE, fg=BG, relief="flat", font=(FONT, 11, "bold"))
        self.open_button.pack(side="left", ipadx=12, ipady=6)
        self.group = tk.StringVar(value=next(iter(GROUPS)))
        selector = ttk.Combobox(toolbar, textvariable=self.group, values=list(GROUPS),
                                state="readonly", width=20)
        selector.pack(side="right")
        selector.bind("<<ComboboxSelected>>", lambda _: self.draw())
        self.info = label(self.body, "Vyber uložený záznam PC Monitoru.", 10, MUTED,
                          bg=BG, wraplength=540, justify="left")
        self.info.pack(anchor="w", pady=6)
        graph = card(self.body)
        graph.pack(fill="x", pady=5)
        self.fig = Figure(figsize=(6, 2.8), dpi=100, facecolor=PANEL)
        self.ax = self.fig.add_subplot(111)
        self.fig.subplots_adjust(left=.13, right=.96, bottom=.21, top=.92)
        self.chart = FigureCanvasTkAgg(self.fig, master=graph)
        self.chart.get_tk_widget().pack(fill="x", padx=8, pady=8)
        table_card = card(self.body)
        table_card.pack(fill="x", pady=5)
        label(table_card, "Statistika dostupných vzorků", 13, TEXT, True).pack(anchor="w", padx=12, pady=8)
        style = ttk.Style(self)
        style.configure("Analysis.Treeview", background=PANEL, fieldbackground=PANEL,
                        foreground=TEXT, rowheight=25, font=(FONT, 10))
        style.configure("Analysis.Treeview.Heading", background=TRACK, foreground=TEXT)
        style.map("Analysis.Treeview.Heading", background=[("pressed", "#284568"), ("active", "#40536b")],
                  foreground=[("pressed", TEXT), ("active", TEXT)])
        style.map("Analysis.Treeview", background=[("selected", "#284568")], foreground=[("selected", TEXT)])
        self.table = ttk.Treeview(table_card, columns=("metric", "min", "avg", "max", "count"),
                                 show="headings", height=9, style="Analysis.Treeview")
        for key, title, width in (("metric", "Metrika", 180), ("min", "Min", 65),
                                  ("avg", "Průměr", 65), ("max", "Max", 65), ("count", "Vzorky", 65)):
            self.table.heading(key, text=title)
            self.table.column(key, width=width, minwidth=45, anchor="w" if key == "metric" else "e",
                              stretch=key == "metric")
        self.table.pack(fill="x", padx=8, pady=(0, 8))
        self.hints = label(self.body, "", 10, MUTED, bg=BG, wraplength=540, justify="left")
        self.hints.pack(anchor="w", pady=10)
        self.draw()

    def open_file(self):
        if self.future is not None:
            return
        path = filedialog.askopenfilename(parent=self, filetypes=[("CSV", "*.csv")])
        if not path:
            return
        self.open_button.configure(state="disabled")
        self.info.configure(text="Načítám " + Path(path).name)
        self.future = self.executor.submit(load_analysis, path)
        self.poll_id = self.after(100, lambda: self.poll(path))

    def poll(self, path):
        self.poll_id = None
        if self.closed:
            return
        if not self.future.done():
            self.poll_id = self.after(100, lambda: self.poll(path))
            return
        try:
            rows, skipped, stats, hints = self.future.result()
        except Exception as exc:
            self.info.configure(text="Načtení selhalo; předchozí analýza zůstala zachována.")
            messagebox.showerror("Nelze načíst záznam", str(exc), parent=self)
        else:
            self.rows = rows
            self.info.configure(text=f"{Path(path).name} · {len(rows)} vzorků · "
                                     f"poslední vzorek {rows[-1]['elapsed_s']:.1f} s · "
                                     f"vynechané řádky: {skipped}")
            self.table.delete(*self.table.get_children())
            for group, metrics in GROUPS.items():
                unit = group[group.index("("):]
                for key, name, _ in metrics:
                    stat = stats[key]
                    values = tuple(f"{v:.2f}" for v in stat[:3]) + (stat[3],) if stat else ("N/A", "N/A", "N/A", 0)
                    self.table.insert("", "end", values=(name + " " + unit, *values))
            self.hints.configure(text="Orientační vyhodnocení:\n" + "\n".join(hints))
            self.draw()
        finally:
            self.future = None
            self.open_button.configure(state="normal")

    def draw(self):
        ax = self.ax
        ax.clear()
        ax.set_facecolor(PANEL)
        ax.tick_params(colors=MUTED, labelsize=9)
        ax.set_xlabel("Uplynulý čas (s)", color=MUTED)
        ax.grid(color=TRACK, alpha=.6)
        for spine in ax.spines.values():
            spine.set_color(TRACK)
        group = self.group.get()
        if group == "Vytížení (%)":
            ax.set_ylim(0, 100)
        else:
            ax.set_ylim(bottom=0)
        if self.rows:
            # Show the full time range; limit plotted points for responsive redraws.
            step = max(1, (len(self.rows) + 9999) // 10000)
            sampled = self.rows[::step]
            if sampled[-1] is not self.rows[-1]:
                sampled.append(self.rows[-1])
            x = [r["elapsed_s"] for r in sampled]
            for key, name, color in GROUPS[group]:
                ax.plot(x, [r[key] if r[key] is not None else float("nan") for r in sampled],
                        color=color, label=name, linewidth=1.2, marker="." if len(x) == 1 else None)
            ax.legend(facecolor=PANEL, edgecolor=TRACK, labelcolor=TEXT)
        else:
            ax.text(.5, .5, "Načti CSV soubor", transform=ax.transAxes, ha="center", color=MUTED)
        self.chart.draw_idle()

    def close(self):
        self.closed = True
        if self.poll_id is not None:
            self.after_cancel(self.poll_id)
        self.executor.shutdown(wait=False, cancel_futures=True)
