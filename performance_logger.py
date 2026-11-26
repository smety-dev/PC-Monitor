"""Local CSV recording of dashboard samples, with no network access."""
import csv
import time
from datetime import datetime

FIELDS = (
    "timestamp", "elapsed_s", "cpu_percent", "ram_percent", "ram_available_mib",
    "gpu_3d_percent", "cpu_frequency_mhz", "disk_read_mib_s",
    "disk_write_mib_s", "net_receive_mib_s", "net_send_mib_s",
)


CSV_HEADERS = (
    "Datum a čas", "Uplynulý čas (s)", "CPU (%)", "RAM (%)",
    "Volná RAM (MiB)", "GPU 3D (%)", "Frekvence CPU (MHz)",
    "Disk čtení (MiB/s)", "Disk zápis (MiB/s)",
    "Síť příjem (MiB/s)", "Síť odesílání (MiB/s)",
)


def excel_number(value):
    if value is None:
        return ""
    return str(value).replace(".", ",")


def excel_row(row):
    stamp = datetime.fromisoformat(row["timestamp"])
    return [stamp.strftime("%d.%m.%Y %H:%M:%S"), 
            *(excel_number(row[key]) for key in FIELDS[1:])]


def make_row(elapsed, cpu, ram_percent, ram_available, gpu, advanced, timestamp=None):
    advanced = advanced or {}
    disk = advanced.get("disk_rates") or (None, None)
    net = advanced.get("net_rates") or (None, None)
    def mib(value):
        return None if value is None else round(value / 1024**2, 3)
    return dict(zip(FIELDS, (
        timestamp or datetime.now().astimezone().isoformat(timespec="milliseconds"),
        round(elapsed, 3), cpu, ram_percent, mib(ram_available), gpu,
        advanced.get("frequency"), *(mib(v) for v in disk + net),
    )))


class PerformanceRecorder:
    def __init__(self, clock=time.monotonic):
        self.clock = clock
        self.file = None
        self.writer = None
        self.path = None
        self.count = 0
        self.interval = 1
        self.started = None
        self.next_sample = None
        self.elapsed = 0

    @property
    def active(self):
        return self.file is not None

    def start(self, path, interval=1):
        if self.active:
            raise RuntimeError("Recording already active")
        if interval not in (1, 2, 5, 10):
            raise ValueError("Unsupported interval")
        # Exclusive creation prevents accidental overwrite.
        file = open(path, "x", newline="", encoding="utf-8-sig")
        try:
            writer = csv.writer(file, delimiter=";")
            writer.writerow(CSV_HEADERS)
            file.flush()
        except Exception:
            file.close()
            raise
        self.file, self.writer, self.path = file, writer, path
        self.count, self.interval, self.elapsed = 0, interval, 0
        self.started = self.next_sample = self.clock()

    def record(self, cpu, ram_percent, ram_available, gpu, advanced):
        if not self.active:
            return False
        now = self.clock()
        self.elapsed = now - self.started
        if now < self.next_sample:
            return False
        self.writer.writerow(excel_row(make_row(self.elapsed, cpu, ram_percent,
                                      ram_available, gpu, advanced)))
        self.file.flush()
        self.count += 1
        # Skip missed periods rather than inventing historical samples.
        self.next_sample += (int((now - self.next_sample) / self.interval) + 1) * self.interval
        return True

    def stop(self):
        if self.active:
            self.elapsed = self.clock() - self.started
            file, self.file = self.file, None
            self.writer = None
            file.close()
