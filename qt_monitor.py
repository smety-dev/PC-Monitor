"""Background system sampling shared by the Qt pages."""
import math
import threading
import subprocess
import time
import psutil
from hardware_metrics import Sampler
from process_metrics import ProcessSampler
from diagnostics import LOG


GPU_COMMAND = r"""
$ErrorActionPreference = 'Stop'
Get-Counter '\GPU Engine(*engtype_3D)\Utilization Percentage' -SampleInterval 2 -Continuous |
ForEach-Object {
    $value = $_.CounterSamples |
        Group-Object { $_.InstanceName -replace '^pid_\d+_', '' } |
        ForEach-Object { ($_.Group | Measure-Object -Property CookedValue -Sum).Sum } |
        Measure-Object -Maximum | Select-Object -ExpandProperty Maximum
    if ($null -ne $value) {
        [Console]::WriteLine(([double]$value).ToString([Globalization.CultureInfo]::InvariantCulture))
    } else {
        [Console]::WriteLine('N/A')
    }
}
"""


def gpu_value(line):
    try:
        value = float(line.strip().replace(",", "."))
    except ValueError:
        return None
    return round(min(100.0, value), 1) if math.isfinite(value) and value >= 0 else None


class Monitor:
    def __init__(self):
        self.stop_event = threading.Event()
        self.gaming = threading.Event()
        self.process_visible = threading.Event()
        self.basic = None
        self.advanced = None
        self.processes = None
        self._gpu_sample = (None, 0.0)
        self.hardware = "Detekuji hardware…"
        self.children = set()
        self.child_lock = threading.Lock()
        self.threads = []

    @property
    def gpu(self):
        value, stamp = self._gpu_sample
        return value if time.monotonic() - stamp <= 8 else None

    def start(self):
        if self.threads:
            return
        for target in (self.system, self.process_worker, self.gpu_worker, self.hardware_worker):
            thread = threading.Thread(target=target, daemon=True, name=target.__name__)
            self.threads.append(thread)
            thread.start()

    def close(self):
        self.stop_event.set()
        with self.child_lock:
            for child in self.children:
                try:
                    child.terminate()
                except OSError:
                    pass
        deadline = time.monotonic() + 1
        for thread in self.threads:
            thread.join(max(0, deadline - time.monotonic()))
        with self.child_lock:
            for child in self.children:
                try:
                    child.kill()
                except OSError:
                    pass

    def set_gaming(self, enabled):
        if enabled:
            self.gaming.set()
            self.processes = None
        else:
            self.gaming.clear()

    def set_process_visible(self, visible):
        if visible:
            self.process_visible.set()
        else:
            self.process_visible.clear()
            self.processes = None

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
        sampler = None
        while not self.stop_event.is_set():
            if self.gaming.is_set() or not self.process_visible.is_set():
                self.processes = None
                sampler = None
                self.stop_event.wait(.25)
                continue
            if sampler is None:
                sampler = ProcessSampler()
            try:
                rows = sampler.sample()
                self.processes = rows if self.process_visible.is_set() and not self.gaming.is_set() else None
            except (psutil.Error, OSError, NotImplementedError):
                self.processes = None
            self.stop_event.wait(2)

    def launch(self, command):
        with self.child_lock:
            if self.stop_event.is_set():
                return None
            child = subprocess.Popen(
                ["powershell", "-NoProfile", "-NonInteractive", "-Command", command],
                stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, text=True,
                errors="replace", creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0))
            self.children.add(child)
            return child

    def release(self, child):
        try:
            if child.poll() is None:
                child.kill()
            child.wait(timeout=1)
        except (OSError, subprocess.SubprocessError):
            pass
        finally:
            if child.stdout:
                child.stdout.close()
            with self.child_lock:
                self.children.discard(child)

    def hardware_worker(self):
        child = None
        try:
            child = self.launch("""
Get-CimInstance Win32_Processor | Select-Object -ExpandProperty Name
Get-CimInstance Win32_VideoController | Select-Object -ExpandProperty Name
""")
            if child is not None:
                output, _ = child.communicate(timeout=10)
                if child.returncode:
                    raise OSError("Hardware query failed")
                self.hardware = output.strip().replace("\n", "  ·  ") or "Detekce hardwaru nedostupná"
        except (OSError, subprocess.SubprocessError):
            self.hardware = "Detekce hardwaru nedostupná"
            if not self.stop_event.is_set():
                LOG.warning("Hardware detection failed")
        finally:
            if child is not None:
                self.release(child)

    def gpu_worker(self):
        # One continuous counter session instead of repeatedly launching PowerShell.
        delay = 2
        while not self.stop_event.is_set():
            child = None
            received = False
            try:
                child = self.launch(GPU_COMMAND)
                if child is None:
                    return
                for line in child.stdout:
                    if self.stop_event.is_set():
                        break
                    self._gpu_sample = (gpu_value(line), time.monotonic())
                    received = True
                if not self.stop_event.is_set():
                    LOG.warning("GPU counter stream ended; retrying")
            except (OSError, subprocess.SubprocessError):
                if not self.stop_event.is_set():
                    LOG.warning("GPU counter stream unavailable; retrying")
            finally:
                self._gpu_sample = (None, 0.0)
                if child is not None:
                    self.release(child)
            delay = 2 if received else min(30, delay * 2)
            self.stop_event.wait(delay)
