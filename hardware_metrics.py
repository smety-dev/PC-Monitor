"""Read-only system metrics, without administrator privileges."""
import time
import psutil


def safe_read(fn, *args, **kwargs):
    try:
        return fn(*args, **kwargs)
    except (OSError, psutil.Error, NotImplementedError):
        return None


def rates(previous, current, elapsed):
    """Compute byte rates from cumulative counters; ignore resets."""
    if previous is None or current is None or elapsed <= 0:
        return None
    if any(b < a for a, b in zip(previous, current)):
        return None
    return tuple((b - a) / elapsed for a, b in zip(previous, current))


class Sampler:
    def __init__(self):
        self.previous = None
        psutil.cpu_percent(percpu=True)

    def sample(self):
        now = time.monotonic()
        disk = safe_read(psutil.disk_io_counters)
        net = safe_read(psutil.net_io_counters)
        disk_pair = (disk.read_bytes, disk.write_bytes) if disk else None
        net_pair = (net.bytes_recv, net.bytes_sent) if net else None
        disk_rates = net_rates = None
        if self.previous:
            old_time, old_disk, old_net = self.previous
            disk_rates = rates(old_disk, disk_pair, now - old_time)
            net_rates = rates(old_net, net_pair, now - old_time)
        self.previous = now, disk_pair, net_pair

        frequency = safe_read(psutil.cpu_freq)
        drives = []
        for partition in safe_read(psutil.disk_partitions, all=False) or []:
            if "cdrom" in partition.opts or "remote" in partition.opts:
                continue
            usage = safe_read(psutil.disk_usage, partition.mountpoint)
            if usage is not None:
                drives.append((partition.mountpoint, usage.used, usage.total, usage.percent))

        return {
            "cores": safe_read(psutil.cpu_percent, percpu=True) or [],
            "frequency": frequency.current if frequency else None,
            "disk_rates": disk_rates,
            "net_rates": net_rates,
            "drives": drives,
        }
