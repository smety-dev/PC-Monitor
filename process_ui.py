"""Searchable, sortable read-only process table."""
import tkinter as tk
from tkinter import ttk
from dashboard_ui import BG, PANEL, TRACK, TEXT, MUTED, BLUE, FONT, label
from process_metrics import filter_sort


class ProcessPage(tk.Frame):
    def __init__(self, parent):
        super().__init__(parent, bg=BG)
        self.rows = None
        self.key = "cpu"
        self.descending = True
        self.query = tk.StringVar()
        tools = tk.Frame(self, bg=BG)
        tools.pack(fill="x", pady=(0, 10))
        label(tools, "Hledat název nebo PID:", 10, MUTED, bg=BG).pack(side="left", padx=(0, 8))
        entry = tk.Entry(tools, textvariable=self.query, bg=PANEL, fg=TEXT,
                         insertbackground=TEXT, relief="flat", font=(FONT, 11))
        entry.pack(side="left", fill="x", expand=True, ipady=6)
        self.status = label(self, "Čekám na první vzorek…", 10, MUTED, bg=BG)
        self.status.pack(anchor="w", pady=(0, 8))

        style = ttk.Style(self)
        style.configure("Processes.Treeview", background=PANEL, fieldbackground=PANEL,
                        foreground=TEXT, rowheight=28, borderwidth=0, font=(FONT, 10))
        style.configure("Processes.Treeview.Heading", background=TRACK,
                        foreground=TEXT, font=(FONT, 10, "bold"), relief="flat")
        style.map("Processes.Treeview", background=[("selected", "#284568")],
                  foreground=[("selected", TEXT)])
        frame = tk.Frame(self, bg=BG)
        frame.pack(fill="both", expand=True)
        self.table = ttk.Treeview(frame, columns=("name", "pid", "cpu", "rss"),
                                 show="headings", style="Processes.Treeview",
                                 selectmode="browse")
        self.columns = {"name": "Proces", "pid": "PID", "cpu": "CPU (%)", "rss": "RAM (MiB)"}
        for key, title in self.columns.items():
            self.table.heading(key, text=title, command=lambda k=key: self.sort_by(k))
        self.table.column("name", width=230, minwidth=110, stretch=True)
        for key, width in (("pid", 65), ("cpu", 85), ("rss", 110)):
            self.table.column(key, width=width, minwidth=60, anchor="e", stretch=False)
        scrollbar = ttk.Scrollbar(frame, orient="vertical", command=self.table.yview,
                                  style="Dark.Vertical.TScrollbar")
        self.table.configure(yscrollcommand=scrollbar.set)
        scrollbar.pack(side="right", fill="y")
        self.table.pack(side="left", fill="both", expand=True)
        label(self, "CPU = podíl celkové kapacity CPU · RAM = pracovní sada (RSS) · N/A = nedostupné",
              9, MUTED, bg=BG, wraplength=550, justify="left").pack(anchor="w", pady=8)
        self.query.trace_add("write", lambda *_: self.render())
        self.update_headings()

    def update_headings(self):
        for key, title in self.columns.items():
            suffix = (" ▼" if self.descending else " ▲") if key == self.key else ""
            self.table.heading(key, text=title + suffix)

    def sort_by(self, key):
        if self.key == key:
            self.descending = not self.descending
        else:
            self.key = key
            self.descending = key in ("cpu", "rss")
        self.update_headings()
        self.render()

    def set_rows(self, rows):
        if rows is self.rows:
            return
        self.rows = rows
        self.render()

    def render(self):
        rows = filter_sort(self.rows or (), self.query.get(), self.key, self.descending)
        selected = self.table.selection()
        position = self.table.yview()[0]
        wanted = {str(row.pid) for row in rows}
        for iid in self.table.get_children():
            if iid not in wanted:
                self.table.delete(iid)
        for index, row in enumerate(rows):
            iid = str(row.pid)
            values = (row.name, row.pid,
                      "N/A" if row.cpu is None else f"{row.cpu:.1f}",
                      "N/A" if row.rss is None else f"{row.rss / 1024**2:.1f}")
            if self.table.exists(iid):
                self.table.item(iid, values=values)
                self.table.move(iid, "", index)
            else:
                self.table.insert("", index, iid=iid, values=values)
        if selected and self.table.exists(selected[0]):
            self.table.selection_set(selected[0])
        self.table.yview_moveto(position)
        self.status.configure(text="Čekám na vzorek / údaje nedostupné" if self.rows is None else
                              f"Zobrazeno {len(rows)} z {len(self.rows)} procesů")
