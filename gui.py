import tkinter as tk
from tkinter import ttk
import psutil
import subprocess
import threading
import time
from collections import deque
from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from version import __version__
from hardware_metrics import Sampler
from process_metrics import ProcessSampler
from process_ui import ProcessPage
from logging_ui import LoggingPage
from analysis_ui import AnalysisPage
from dashboard_ui import (
    BG, PANEL, TRACK, TEXT, MUTED, BLUE, ORANGE, GREEN, FONT,
    Gauge, ScrollPage, card, label, configure_style, chart_style, SIDEBAR, HOVER, SELECTED,
)

gpu_usage = None
advanced_sample = None
process_rows = None
hardware_name = None
history = [deque(maxlen=60) for _ in range(3)]
stop = threading.Event()

def get_hardware():
    command = """
    Get-CimInstance Win32_Processor |
    Select-Object -ExpandProperty Name

    Get-CimInstance Win32_VideoController |
    Select-Object -ExpandProperty Name
    """

    try:
        result = subprocess.check_output(
            ["powershell", "-NoProfile", "-Command", command],
            text=True,
            timeout=10,
            creationflags=subprocess.CREATE_NO_WINDOW
        )

        return result.strip()

    except (OSError, subprocess.SubprocessError):
        return "Hardware detection unavailable"

def gpu_worker():
    global gpu_usage

    command = r"""
    (Get-Counter '\GPU Engine(*engtype_3D)\Utilization Percentage').CounterSamples |
    Group-Object { $_.InstanceName -replace '^pid_\d+_', '' } |
    ForEach-Object {
        ($_.Group | Measure-Object -Property CookedValue -Sum).Sum
    } |
    Measure-Object -Maximum |
    Select-Object -ExpandProperty Maximum
    """

    while not stop.is_set():
        try:
            result = subprocess.check_output(
                ["powershell", "-NoProfile", "-Command", command],
                text=True,
                timeout=10,
                creationflags=subprocess.CREATE_NO_WINDOW
            )

            gpu_usage = round(
                float(result.strip().replace(",", ".")), 1
            )

        except (ValueError, OSError, subprocess.SubprocessError):
            gpu_usage = None

        stop.wait(2)



def advanced_worker():
    global advanced_sample
    sampler = Sampler()
    while not stop.is_set():
        try:
            advanced_sample = sampler.sample()
        except (OSError, psutil.Error, NotImplementedError):
            advanced_sample = None
        stop.wait(2)


def process_worker():
    global process_rows
    sampler = ProcessSampler()
    while not stop.is_set():
        try:
            process_rows = sampler.sample()
        except (OSError, psutil.Error, NotImplementedError):
            process_rows = None
        stop.wait(2)


def hardware_worker():
    global hardware_name
    hardware_name = get_hardware()


root = tk.Tk()
root.title(f"PC Monitor v{__version__}")
root.geometry("1200x800")
root.minsize(800, 620)
root.configure(bg=BG)
configure_style(root)

sidebar = tk.Frame(root, bg=SIDEBAR, width=190)
sidebar.pack(side="left", fill="y")
sidebar.pack_propagate(False)
label(sidebar, "▰  PC Monitor", 17, TEXT, True, SIDEBAR).pack(anchor="w", padx=18, pady=(24, 4))
label(sidebar, f"DESKTOP  /  v{__version__}", 9, MUTED, bg=SIDEBAR).pack(anchor="w", padx=16)
label(sidebar, "MONITORING", 9, MUTED, True, SIDEBAR).pack(anchor="w", padx=16, pady=(35, 10))

main = tk.Frame(root, bg=BG)
main.pack(side="left", fill="both", expand=True, padx=24, pady=20)
heading = label(main, "Přehled systému", 25, TEXT, True, BG)
heading.pack(anchor="w")
hardware_label = label(main, "Detekuji hardware…", 10, MUTED, bg=BG,
                       justify="left", wraplength=650)
hardware_label.pack(anchor="w", pady=(3, 14))

page_host = tk.Frame(main, bg=BG)
page_host.pack(fill="both", expand=True)
pages = {}
buttons = {}
active_page = "Přehled"
for name in ("Přehled", "Procesor", "Disky", "Síť", "Procesy", "Záznam", "Analýza"):
    if name == "Přehled":
        pages[name] = tk.Frame(page_host, bg=BG)
    elif name == "Procesy":
        pages[name] = ProcessPage(page_host)
    elif name == "Záznam":
        pages[name] = LoggingPage(page_host)
    elif name == "Analýza":
        pages[name] = AnalysisPage(page_host)
    else:
        pages[name] = ScrollPage(page_host)

def show_page(name):
    global active_page
    active_page = name
    for key, page in pages.items():
        page.pack_forget()
        buttons[key].configure(bg=SELECTED if key == name else SIDEBAR,
                               fg=BLUE if key == name else MUTED)
    pages[name].pack(fill="both", expand=True)
    heading.configure(text={"Přehled": "Přehled systému", "Procesor": "Procesor",
                            "Disky": "Úložiště", "Síť": "Síťový provoz", "Procesy": "Správce procesů", "Záznam": "Záznam výkonu", "Analýza": "Analýza výkonu"}[name])
    if name == "Přehled":
        graph_canvas.draw_idle()
    elif name == "Procesy":
        pages[name].set_rows(process_rows)

nav_icons = {"Přehled": "▦", "Procesor": "▣", "Disky": "▤", "Síť": "↔",
             "Procesy": "≡", "Záznam": "●", "Analýza": "▥"}
for name in pages:
    button = tk.Button(sidebar, text=f"{nav_icons[name]}    {name}", anchor="w", padx=14, pady=10,
                       bg=SIDEBAR, fg=MUTED, activebackground=HOVER,
                       activeforeground=TEXT, relief="flat", bd=0, cursor="hand2",
                       font=(FONT, 11), command=lambda n=name: show_page(n))
    button.pack(fill="x", padx=10, pady=2)
    button.bind("<Enter>", lambda e, n=name: e.widget.configure(bg=SELECTED if n == active_page else HOVER))
    button.bind("<Leave>", lambda e, n=name: e.widget.configure(bg=SELECTED if n == active_page else SIDEBAR))
    buttons[name] = button
label(sidebar, "●  Živé měření", 10, GREEN, bg=SIDEBAR).pack(side="bottom", anchor="w",
                                                padx=15, pady=20)

overview = pages["Přehled"]
gauges = []
gauge_row = tk.Frame(overview, bg=BG)
gauge_row.pack(fill="x")
for i, (name, color) in enumerate((("CPU", BLUE), ("RAM", ORANGE), ("GPU 3D", GREEN))):
    gauge_row.columnconfigure(i, weight=1, uniform="gauge")
    gauge = Gauge(gauge_row, name, color)
    gauge.grid(row=0, column=i, sticky="nsew", padx=4)
    gauges.append(gauge)

summary = label(overview, "", 10, MUTED, bg=BG, justify="left")
summary.pack(anchor="w", pady=12)
graph_panel = card(overview)
graph_panel.pack(fill="both", expand=True)
label(graph_panel, "Historie vytížení", 12, TEXT, True).pack(anchor="w", padx=12, pady=(10, 0))
fig = Figure(figsize=(6, 3), dpi=100, facecolor=PANEL)
ax = fig.add_subplot(111)
chart_style(ax)
ax.set_ylim(0, 100)
ax.set_xlim(-59, 0)
ax.set_ylabel("%", color=MUTED)
graph_lines = [ax.plot([], [], color=color, label=name, linewidth=2.0)[0]
               for name, color in (("CPU", BLUE), ("RAM", ORANGE), ("GPU 3D", GREEN))]
ax.legend(frameon=False, labelcolor=TEXT, loc="upper left", ncol=3)
fig.subplots_adjust(left=.10, right=.97, top=.94, bottom=.13)
graph_canvas = FigureCanvasTkAgg(fig, master=graph_panel)
graph_canvas.get_tk_widget().pack(fill="both", expand=True, padx=8, pady=8)
label(graph_panel, "Posledních 60 vzorků  ·  nejnovější vpravo", 9, MUTED).pack(pady=(0, 8))

cpu_body = pages["Procesor"].body
cpu_card = card(cpu_body)
cpu_card.pack(fill="x", pady=5)
frequency_label = label(cpu_card, "Frekvence: čekám na data", 19, BLUE, True)
frequency_label.pack(anchor="w", padx=14, pady=(14, 4))
label(cpu_card, "Frekvence hlášená OS · nemusí být okamžitá", 10, MUTED).pack(anchor="w", padx=14)
label(cpu_card, f"{psutil.cpu_count(logical=False)} fyzických jader / {psutil.cpu_count()} logických procesorů",
      11).pack(anchor="w", padx=14, pady=12)
core_card = card(cpu_body)
core_card.pack(fill="x", pady=5)
label(core_card, "Vytížení logických procesorů", 13, TEXT, True).pack(anchor="w", padx=14, pady=12)
core_grid = tk.Frame(core_card, bg=PANEL)
core_grid.pack(fill="x", padx=10, pady=(0, 12))
core_widgets = []

disk_body = pages["Disky"].body
disk_rates_card = card(disk_body)
disk_rates_card.pack(fill="x", pady=5)
disk_rates_label = label(disk_rates_card, "Čtení / zápis: čekám na data", 16, BLUE, True)
disk_rates_label.pack(anchor="w", padx=14, pady=15)
label(disk_rates_card, "Celkový provoz všech disků", 10, MUTED).pack(anchor="w", padx=14, pady=(0, 12))
drive_host = tk.Frame(disk_body, bg=BG)
drive_host.pack(fill="x")
drive_widgets = {}
drive_empty = label(drive_host, "Žádné dostupné místní disky", 11, MUTED, bg=BG)
drive_empty.pack(anchor="w", pady=10)

net_body = pages["Síť"].body
net_card = card(net_body)
net_card.pack(fill="x", pady=5)
label(net_card, "Celkový síťový provoz", 13, TEXT, True).pack(anchor="w", padx=14, pady=12)
net_labels = []
for name, color in (("Příjem", BLUE), ("Odesílání", GREEN)):
    label(net_card, name, 11, MUTED).pack(anchor="w", padx=14, pady=(8, 0))
    val = label(net_card, "N/A", 24, color, True)
    val.pack(anchor="w", padx=14, pady=(0, 12))
    net_labels.append(val)


def format_rate(value):
    return "N/A" if value is None else f"{value / 1024**2:.2f} MiB/s"


def update_details(sample):
    cores = sample["cores"] if sample else []
    freq = sample["frequency"] if sample else None
    frequency_label.configure(text=f"Frekvence: {freq:.0f} MHz" if freq else "Frekvence: nedostupná")
    if len(core_widgets) != len(cores):
        for child in core_grid.winfo_children():
            child.destroy()
        core_widgets.clear()
        for i in range(len(cores)):
            col = i % 2
            core_grid.columnconfigure(col, weight=1)
            frame = tk.Frame(core_grid, bg=PANEL)
            frame.grid(row=i//2, column=col, sticky="ew", padx=8, pady=6)
            value_label = label(frame, f"CPU {i}", 10)
            value_label.pack(anchor="w")
            bar = ttk.Progressbar(frame, maximum=100, orient="horizontal", style="Dashboard.Horizontal.TProgressbar")
            bar.pack(fill="x", pady=3)
            core_widgets.append((value_label, bar))
    for i, (value, widgets) in enumerate(zip(cores, core_widgets)):
        widgets[0].configure(text=f"CPU {i:02d}   {value:.1f}%")
        widgets[1]["value"] = value

    disk_rates = sample["disk_rates"] if sample else None
    read, write = disk_rates if disk_rates else (None, None)
    disk_rates_label.configure(text=f"Čtení: {format_rate(read)}   |   Zápis: {format_rate(write)}")
    drives = sample["drives"] if sample else []
    if drives:
        drive_empty.pack_forget()
    elif not drive_empty.winfo_manager():
        drive_empty.pack(anchor="w", pady=10)
    mounts = {entry[0] for entry in drives}
    for mount in list(drive_widgets):
        if mount not in mounts:
            drive_widgets.pop(mount)[0].destroy()
    for mount, used, total, percent in drives:
        if mount not in drive_widgets:
            frame = card(drive_host)
            frame.pack(fill="x", pady=5)
            label(frame, f"Disk {mount}", 13, TEXT, True).pack(anchor="w", padx=14, pady=(12, 4))
            val = label(frame, "", 11, MUTED)
            val.pack(anchor="w", padx=14)
            bar = ttk.Progressbar(frame, maximum=100, orient="horizontal", style="Dashboard.Horizontal.TProgressbar")
            bar.pack(fill="x", padx=14, pady=12)
            drive_widgets[mount] = frame, val, bar
        _, val, bar = drive_widgets[mount]
        val.configure(text=f"{used/1024**3:.1f} / {total/1024**3:.1f} GiB  ·  {percent:.1f}%")
        bar["value"] = percent

    net_rates = sample["net_rates"] if sample else None
    for val, rate in zip(net_labels, net_rates or (None, None)):
        val.configure(text=format_rate(rate))


def update():
    cpu = psutil.cpu_percent(interval=None)
    ram = psutil.virtual_memory()
    gpu = gpu_usage
    pages["Záznam"].capture(cpu, ram, gpu, advanced_sample)
    if hardware_name is not None:
        hardware_label.configure(text=hardware_name)
    for gauge, value, caption in zip(
        gauges, (cpu, ram.percent, gpu),
        ("Vytížení procesoru", f"{ram.available/1024**3:.2f} GiB dostupné",
         "Nejvytíženější 3D jednotka"),
    ):
        gauge.update_value(value, caption)
    summary.configure(text=f"RAM: {ram.total/1024**3:.2f} GiB  ·  "
                           f"CPU: {psutil.cpu_count(logical=False)} jader / {psutil.cpu_count()} vláken")
    for series, line, value in zip(history, graph_lines, (cpu, ram.percent, gpu)):
        series.append(value)
        line.set_data(range(1-len(series), 1), list(series))
    if active_page == "Přehled":
        graph_canvas.draw_idle()
    elif active_page == "Procesy":
        pages["Procesy"].set_rows(process_rows)
    elif active_page in ("Procesor", "Disky", "Síť"):
        update_details(advanced_sample)
    root.after(1000, update)


def close():
    stop.set()
    pages["Záznam"].finish()
    pages["Analýza"].close()
    root.destroy()


root.protocol("WM_DELETE_WINDOW", close)
for worker in (gpu_worker, advanced_worker, hardware_worker, process_worker):
    threading.Thread(target=worker, daemon=True).start()
psutil.cpu_percent()
show_page("Přehled")
update()
root.mainloop()
