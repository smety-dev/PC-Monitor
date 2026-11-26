
import tkinter as tk
from tkinter import ttk
import psutil
from version import __version__
from hardware_metrics import Sampler
import subprocess
import threading
import time
from collections import deque
from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

BG = "#10151f"
PANEL = "#1c2432"

gpu_usage = None
advanced_sample = None
cpu_history = deque(maxlen=60)
ram_history = deque(maxlen=60)
gpu_history = deque(maxlen=60)


root = tk.Tk()
root.title(f"PC Monitor v{__version__}")
root.geometry("760x850")
root.minsize(600, 650)
root.configure(bg=BG)

style = ttk.Style()
style.theme_use("clam")
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

def create_meter(name, color):
    frame = tk.Frame(root, bg=PANEL)
    frame.pack(fill="x", padx=20, pady=3)

    label = tk.Label(
        frame,
        text=f"{name}: 0 %",
        font=("Arial", 18, "bold"),
        bg=PANEL,
        fg=color
    )
    label.pack(pady=3)

    style_name = f"{name}.Horizontal.TProgressbar"

    style.configure(
        style_name,
        background=color,
        troughcolor="#374151",
        bordercolor=PANEL
    )

    bar = ttk.Progressbar(
        frame,
        style=style_name,
        maximum=100
    )
    bar.pack(fill="x", padx=15, pady=4)

    return label, bar


title = tk.Label(
    root,
    text="PC Monitor",
    font=("Arial", 28, "bold"),
    bg=BG,
    fg="white"
)
title.pack(pady=8)
hardware_label = tk.Label(
    root,
    text=get_hardware(),
    font=("Arial", 11),
    bg=BG,
    fg="#94a3b8"
)

hardware_label.pack(pady=5)

cpu_label, cpu_bar = create_meter("CPU", "#60a5fa")
ram_label, ram_bar = create_meter("RAM", "#f59e0b")
gpu_label, gpu_bar = create_meter("GPU", "#4ade80")

info = tk.Label(
    root,
    text="",
    font=("Arial", 13),
    bg=BG,
    fg="white",
    justify="left"
)
info.pack(pady=5)
notebook = ttk.Notebook(root)
notebook.pack(fill="both", expand=True, padx=15, pady=8)
usage_tab = tk.Frame(notebook, bg=BG)
details_tab = tk.Frame(notebook, bg=BG)
notebook.add(usage_tab, text="Vytížení")
notebook.add(details_tab, text="Hardware a síť")

details = tk.Text(details_tab, bg=PANEL, fg="white", font=("Consolas", 11),
                  wrap="word", relief="flat", padx=12, pady=10)
scrollbar = ttk.Scrollbar(details_tab, command=details.yview)
details.configure(yscrollcommand=scrollbar.set, state="disabled")
scrollbar.pack(side="right", fill="y")
details.pack(side="left", fill="both", expand=True)


def advanced_worker():
    global advanced_sample
    sampler = Sampler()
    while True:
        try:
            advanced_sample = sampler.sample()
        except (OSError, psutil.Error, NotImplementedError):
            advanced_sample = None
        time.sleep(2)


def render_details():
    sample = advanced_sample
    if sample is None:
        text = "Čekám na údaje nebo jsou nedostupné."
    else:
        frequency = sample["frequency"]
        freq_text = f"{frequency:.0f} MHz" if frequency else "Nedostupné"
        lines = [f"CPU frekvence (hlášená OS): {freq_text}",
                 "", "LOGICKÉ PROCESORY"]
        for i, value in enumerate(sample["cores"]):
            bar = "█" * min(20, max(0, int(value / 5)))
            lines.append(f"{i:3}: {value:5.1f} %  {bar}")
        if not sample["cores"]:
            lines.append("Nedostupné")
        lines += ["", "DISKY"]
        for mount, used, total, percent in sample["drives"]:
            lines.append(f"{mount}  {used / 1024**3:.1f}/{total / 1024**3:.1f} GiB ({percent:.1f} %)")
        if not sample["drives"]:
            lines.append("Nedostupné")
        lines += ["", "PŘENOS DAT (celkem)"]
        for label, pair, names in (
            ("Disk", sample["disk_rates"], ("Čtení", "Zápis")),
            ("Síť", sample["net_rates"], ("Příjem", "Odesílání")),
        ):
            lines.append(label)
            if pair is None:
                lines.append("  Nedostupné / čekám na další vzorek")
            else:
                for name, value in zip(names, pair):
                    lines.append(f"  {name}: {value / 1024**2:.2f} MiB/s")
        text = "\n".join(lines)
    if details.get("1.0", "end-1c") != text:
        position = details.yview()[0]
        details.configure(state="normal")
        details.delete("1.0", "end")
        details.insert("1.0", text)
        details.configure(state="disabled")
        details.yview_moveto(position)

fig = Figure(figsize=(5, 2), dpi=100)
fig.patch.set_facecolor(BG)

ax = fig.add_subplot(111)
ax.set_facecolor(PANEL)
ax.set_ylim(0, 100)
ax.set_xlim(0, 59)
ax.set_title("Historie vytížení", color="white")
ax.tick_params(colors="white")
ax.grid(alpha=0.2)

line, = ax.plot([], [], color="#60a5fa", label="CPU")
ram_line, = ax.plot([], [], color="#f59e0b", label="RAM")
gpu_line, = ax.plot([], [], color="#4ade80", label="GPU")

ax.legend(facecolor=PANEL, labelcolor="white")

canvas = FigureCanvasTkAgg(fig, master=usage_tab)
canvas.get_tk_widget().pack(fill="both", expand=True)


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

    while True:
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

        time.sleep(1)


def update():
    cpu = psutil.cpu_percent()
    ram = psutil.virtual_memory()
    gpu = gpu_usage

    cpu_history.append(cpu)
    ram_history.append(ram.percent)
    gpu_history.append(gpu)

    cpu_label.config(text=f"CPU: {cpu} %")
    cpu_bar["value"] = cpu

    ram_label.config(text=f"RAM: {ram.percent} %")
    ram_bar["value"] = ram.percent

    if gpu is not None:
        gpu_label.config(text=f"GPU 3D: {gpu} %")
        gpu_bar["value"] = gpu
    else:
        gpu_label.config(text="GPU: Nedostupne")
        gpu_bar["value"] = 0

    info.config(
        text=f"Dostupná RAM: {ram.available / 1024**3:.2f} GB\n"
             f"Celková RAM: {ram.total / 1024**3:.2f} GB\n"
             f"Fyzická jádra: {psutil.cpu_count(logical=False)}\n"
             f"Logická jádra: {psutil.cpu_count()}"
    )
    line.set_data(range(len(cpu_history)), list(cpu_history))
    ram_line.set_data(range(len(ram_history)), list(ram_history))
    gpu_line.set_data(range(len(gpu_history)), list(gpu_history))

    if notebook.select() == str(usage_tab):
        canvas.draw_idle()
    else:
        render_details()

    root.after(1000, update)
    


threading.Thread(
    target=gpu_worker,
    daemon=True
).start()

threading.Thread(target=advanced_worker, daemon=True).start()

psutil.cpu_percent()
update()
root.mainloop()
