"""Background system sampling shared by the Qt pages."""
import threading
import subprocess
import psutil
from hardware_metrics import Sampler
from process_metrics import ProcessSampler


class Monitor:
    def __init__(self):
        self.stop_event = threading.Event()
        self.basic = None
        self.advanced = None
        self.processes = None
        self.gpu = None
        self.hardware = "Detekuji hardware…"

    def start(self):
        for target in (self.system, self.process_worker, self.gpu_worker, self.hardware_worker):
            threading.Thread(target=target, daemon=True).start()

    def close(self):
        self.stop_event.set()

    def system(self):
        sampler = Sampler()
        psutil.cpu_percent()
        while not self.stop_event.wait(1):
            try:
                self.basic = (psutil.cpu_percent(), psutil.virtual_memory())
                self.advanced = sampler.sample()
            except (psutil.Error, OSError, NotImplementedError):
                self.advanced = None

    def process_worker(self):
        sampler = ProcessSampler()
        while not self.stop_event.is_set():
            try:
                self.processes = sampler.sample()
            except (psutil.Error, OSError, NotImplementedError):
                self.processes = None
            self.stop_event.wait(2)

    @staticmethod
    def powershell(command):
        return subprocess.check_output(
            ["powershell", "-NoProfile", "-Command", command],
            text=True, timeout=10, creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0)
        ).strip()

    def hardware_worker(self):
        try:
            self.hardware = self.powershell("""
Get-CimInstance Win32_Processor | Select-Object -ExpandProperty Name
Get-CimInstance Win32_VideoController | Select-Object -ExpandProperty Name
""").replace("\n", "  ·  ")
        except (OSError, subprocess.SubprocessError):
            self.hardware = "Detekce hardwaru nedostupná"

    def gpu_worker(self):
        command = r"""
(Get-Counter '\GPU Engine(*engtype_3D)\Utilization Percentage').CounterSamples |
Group-Object { $_.InstanceName -replace '^pid_\d+_', '' } |
ForEach-Object { ($_.Group | Measure-Object -Property CookedValue -Sum).Sum } |
Measure-Object -Maximum | Select-Object -ExpandProperty Maximum
"""
        while not self.stop_event.is_set():
            try:
                self.gpu = round(float(self.powershell(command).replace(",", ".")), 1)
            except (ValueError, OSError, subprocess.SubprocessError):
                self.gpu = None
            self.stop_event.wait(2)
