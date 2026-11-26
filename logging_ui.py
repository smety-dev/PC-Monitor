"""Dashboard controls for local performance recording."""
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from datetime import datetime
from pathlib import Path
from dashboard_ui import BG, PANEL, TRACK, TEXT, MUTED, BLUE, GREEN, FONT, card, label, action
from performance_logger import PerformanceRecorder


class LoggingPage(tk.Frame):
    def __init__(self, parent):
        super().__init__(parent, bg=BG)
        self.recorder = PerformanceRecorder()
        self.interval = tk.StringVar(value="1")
        panel = card(self)
        panel.pack(fill="x", pady=5)
        label(panel, "Záznam do CSV", 16, TEXT, True).pack(anchor="w", padx=16, pady=(16, 8))
        label(panel, "Interval vzorkování (sekundy)", 11, MUTED).pack(anchor="w", padx=16)
        self.interval_box = ttk.Combobox(panel, textvariable=self.interval,
                                         values=("1", "2", "5", "10"), state="readonly", width=10)
        self.interval_box.pack(anchor="w", padx=16, pady=8)
        controls = tk.Frame(panel, bg=PANEL)
        controls.pack(fill="x", padx=16, pady=12)
        self.start_button = action(controls, "Spustit záznam", self.start)
        self.start_button.pack(side="left", ipadx=12, ipady=6)
        self.stop_button = action(controls, "Zastavit", self.finish, primary=False)
        self.stop_button.pack(side="left", padx=10, ipadx=12, ipady=6)
        self.status = label(panel, "Připraveno", 14, MUTED, True)
        self.status.pack(anchor="w", padx=16, pady=6)
        self.stats = label(panel, "0 vzorků", 22, TEXT, True)
        self.stats.pack(anchor="w", padx=16, pady=6)
        self.path_label = label(panel, "Soubor zatím nebyl vybrán", 10, MUTED,
                                wraplength=520, justify="left")
        self.path_label.pack(anchor="w", padx=16, pady=(6, 16))
        info = card(self)
        info.pack(fill="x", pady=8)
        label(info, "Ukládané údaje", 13, TEXT, True).pack(anchor="w", padx=16, pady=12)
        label(info, "Čas · CPU · RAM · GPU 3D · frekvence CPU\nČtení a zápis disků · příjem a odesílání sítě",
              11, MUTED, justify="left", wraplength=520).pack(anchor="w", padx=16, pady=(0, 10))
        label(info, "Záznam pokračuje i na jiných stránkách. Soubor je místní; nic se neodesílá.",
              10, MUTED, justify="left", wraplength=520).pack(anchor="w", padx=16, pady=(0, 14))
        self.refresh_controls()

    def refresh_controls(self):
        active = self.recorder.active
        self.start_button.configure(state="disabled" if active else "normal")
        self.stop_button.configure(state="normal" if active else "disabled")
        self.interval_box.configure(state="disabled" if active else "readonly")

    def start(self):
        if self.recorder.active:
            return
        path = filedialog.asksaveasfilename(parent=self, defaultextension=".csv",
                    initialfile=datetime.now().strftime("pc-monitor-%Y%m%d-%H%M%S.csv"),
                    filetypes=[("CSV", "*.csv")])
        if not path:
            return
        try:
            self.recorder.start(path, int(self.interval.get()))
        except (OSError, ValueError, RuntimeError) as exc:
            messagebox.showerror("Nelze spustit záznam", str(exc), parent=self)
            return
        self.path_label.configure(text=str(Path(path)))
        self.status.configure(text="● Probíhá záznam", fg=GREEN)
        self.refresh_controls()
        self.update_stats()

    def update_stats(self):
        self.stats.configure(text=f"{self.recorder.count} vzorků  ·  {self.recorder.elapsed:.0f} s")

    def finish(self):
        try:
            self.recorder.stop()
            self.status.configure(text="Záznam ukončen", fg=MUTED)
        except OSError as exc:
            self.status.configure(text=f"Chyba při uzavření: {exc}", fg="#f87171")
        self.refresh_controls()
        self.update_stats()

    def capture(self, cpu, ram, gpu, advanced):
        if not self.recorder.active:
            return
        try:
            self.recorder.record(cpu, ram.percent, ram.available, gpu, advanced)
            self.update_stats()
        except (OSError, ValueError) as exc:
            self.finish()
            self.status.configure(text=f"Chyba zápisu: {exc}", fg="#f87171")
