
import tkinter as tk
from tkinter import ttk
import psutil
from version import __version__
from temperatures import read_temperatures
import subprocess
import threading
import time
from collections import deque
from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

BG = "#10151f"
PANEL = "#1c2432"

gpu_usage = None
temperature_sample = (None, None)
cpu_temp_history = deque(maxlen=60)
gpu_temp_history = deque(maxlen=60)
peak_cpu = peak_gpu = None
cpu_history = deque(maxlen=60)
ram_history = deque(maxlen=60)
gpu_history = deque(maxlen=60)


root = tk.Tk()
root.title(f"PC Monitor v{__version__}")
root.geometry("720x850")
root.minsize(580, 650)
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
temp_tab = tk.Frame(notebook, bg=BG)
notebook.add(usage_tab, text="Vytizeni")
notebook.add(temp_tab, text="Teploty")
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

temp_labels = []
for name in ("CPU", "GPU"):
    label = tk.Label(temp_tab, text=f"{name}: Nedostupne",
                     bg=BG, fg="white", font=("Arial", 13))
    label.pack(pady=2)
    temp_labels.append(label)

temp_status = tk.Label(temp_tab, text="LibreHardwareMonitor: cekam na data",
                       bg=BG, fg="#94a3b8", wraplength=500)
temp_status.pack(pady=2)

temp_fig = Figure(figsize=(5, 2), dpi=100)
temp_fig.patch.set_facecolor(BG)
temp_ax = temp_fig.add_subplot(111)
temp_ax.set_facecolor(PANEL)
temp_ax.set_xlim(0, 59)
temp_ax.set_ylim(-10, 120)
temp_ax.set_ylabel("°C", color="white")
temp_ax.tick_params(colors="white")
temp_ax.grid(alpha=0.2)
cpu_temp_line, = temp_ax.plot([], [], color="#60a5fa", label="CPU")
gpu_temp_line, = temp_ax.plot([], [], color="#4ade80", label="GPU")
temp_ax.legend(facecolor=PANEL, labelcolor="white")
temp_fig.tight_layout()
temp_canvas = FigureCanvasTkAgg(temp_fig, master=temp_tab)
temp_canvas.get_tk_widget().pack(fill="both", expand=True)


def temperature_worker():
    global temperature_sample
    while True:
        temperature_sample = read_temperatures()
        time.sleep(3)


def update_temperatures():
    global peak_cpu, peak_gpu
    cpu_temp, gpu_temp = temperature_sample
    cpu_temp_history.append(cpu_temp)
    gpu_temp_history.append(gpu_temp)
    if cpu_temp is not None:
        peak_cpu = cpu_temp if peak_cpu is None else max(peak_cpu, cpu_temp)
    if gpu_temp is not None:
        peak_gpu = gpu_temp if peak_gpu is None else max(peak_gpu, gpu_temp)
    for name, label, value, peak in zip(
        ("CPU", "GPU"), temp_labels, (cpu_temp, gpu_temp), (peak_cpu, peak_gpu)
    ):
        current = "Nedostupne" if value is None else f"{value:.1f} °C"
        maximum = "—" if peak is None else f"{peak:.1f} °C"
        color = "#94a3b8" if value is None else (
            "#f87171" if value >= 90 else "#f59e0b" if value >= 80 else "#4ade80"
        )
        label.config(text=f"{name}: {current}   |   Max: {maximum}", fg=color)
    temp_status.config(text=(
        "Orientační prahy: 80 / 90 °C; limity se liší podle hardwaru."
        if cpu_temp is not None or gpu_temp is not None else
        "Spusť LibreHardwareMonitor; pokud senzory chybí, ověř oprávnění."
    ))
    cpu_temp_line.set_data(range(len(cpu_temp_history)), list(cpu_temp_history))
    gpu_temp_line.set_data(range(len(gpu_temp_history)), list(gpu_temp_history))
    values = [v for v in (*cpu_temp_history, *gpu_temp_history) if v is not None]
    temp_ax.set_ylim(min(-10, min(values, default=0) - 5),
                     max(120, max(values, default=0) + 5))
    if notebook.select() == str(temp_tab):
        temp_canvas.draw_idle()



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
    update_temperatures()

    root.after(1000, update)
    


threading.Thread(
    target=gpu_worker,
    daemon=True
).start()

threading.Thread(target=temperature_worker, daemon=True).start()

psutil.cpu_percent()
update()
root.mainloop()
