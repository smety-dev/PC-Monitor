"""Background system sampling shared by the Qt pages."""
import math
import os
import threading
import subprocess
import time
import psutil
from pc_monitor.core.hardware_metrics import Sampler
from pc_monitor.core.process_metrics import ProcessSampler
from pc_monitor.core.diagnostics import LOG


GPU_COMMAND = r"""
$ErrorActionPreference = 'Stop'
function Write-GpuSample($samples, $nameProperty, $valueProperty) {
    $totals = @{}
    foreach ($sample in $samples) {
        $name = $sample.$nameProperty
        $value = $sample.$valueProperty
        if ($name -match '_engtype_3D$' -and $null -ne $value -and
            $value -ge 0 -and -not [double]::IsInfinity($value)) {
            $engine = $name -replace '^pid_\d+_', ''
            $totals[$engine] += [double]$value
        }
    }
    if ($totals.Count -eq 0) {
        [Console]::WriteLine('N/A')
        return
    }
    $maximum = 0.0
    foreach ($total in $totals.Values) {
        $maximum = [Math]::Max($maximum, $total)
    }
    [Console]::WriteLine($maximum.ToString([Globalization.CultureInfo]::InvariantCulture))
}

try {
    Get-Counter '\GPU Engine(*)\Utilization Percentage' -SampleInterval 2 -Continuous |
        ForEach-Object { Write-GpuSample $_.CounterSamples InstanceName CookedValue }
} catch {
    [Console]::WriteLine('GPU_ERROR: Get-Counter: ' + ($_.Exception.Message -replace '\s+', ' '))
    # WMI class and property names do not depend on localized counter names.
    try {
        while ($true) {
            $samples = Get-CimInstance -ClassName Win32_PerfFormattedData_GPUPerformanceCounters_GPUEngine
            Write-GpuSample $samples Name UtilizationPercentage
            Start-Sleep -Seconds 2
        }
    } catch {
        [Console]::WriteLine('GPU_ERROR: WMI: ' + ($_.Exception.Message -replace '\s+', ' '))
        exit 1
    }
}
"""


def gpu_value(line):
    try:
        value = float(line.strip().replace(",", "."))
    except ValueError:
        return None
    return round(min(100.0, value), 1) if math.isfinite(value) and value >= 0 else None


def hardware_names(output):
    """Keep processor and display adapter names separate, without guessing adapter IDs."""
    cpus, gpus = [], []
    for line in output.splitlines():
        kind, sep, name = line.partition(":")
        name = name.strip()
        if sep and name:
            if kind.strip() == "CPU":
                cpus.append(name)
            elif kind.strip() == "GPU":
                gpus.append(name)
    return tuple(cpus), tuple(gpus)


def gpu_description(names):
    if len(names) == 1:
        return names[0]
    if len(names) > 1:
        return "Více GPU · maximum 3D"
    return "Název GPU nedostupný"


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
        self.gpu_names = ()
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
            env = os.environ.copy()
            # Windows PowerShell must discover its own modules when launched from PowerShell 7.
            env.pop("PSMODULEPATH", None)
            env.pop("PSModulePath", None)
            child = subprocess.Popen(
                ["powershell", "-NoProfile", "-NonInteractive", "-Command", command],
                stdin=subprocess.DEVNULL, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, text=True,
                errors="replace", creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0), env=env)
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
Get-CimInstance Win32_Processor | ForEach-Object { 'CPU: ' + $_.Name }
Get-CimInstance Win32_VideoController | ForEach-Object { 'GPU: ' + $_.Name }
""")
            if child is not None:
                output, _ = child.communicate(timeout=10)
                if child.returncode:
                    raise OSError("Hardware query failed")
                cpus, gpus = hardware_names(output)
                self.gpu_names = gpus
                self.hardware = "  ·  ".join(cpus + gpus) or "Detekce hardwaru nedostupná"
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
        reported_errors = set()
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
                    if line.startswith("GPU_ERROR: "):
                        message = line.removeprefix("GPU_ERROR: ").strip()
                        if message not in reported_errors:
                            LOG.warning("GPU counter: %s", message)
                            reported_errors.add(message)
                        continue
                    value = gpu_value(line)
                    self._gpu_sample = (value, time.monotonic())
                    if value is not None:
                        received = True
                        reported_errors.clear()
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
