"""Read-only process monitoring. Missing readings are represented by None."""
from dataclasses import dataclass
import time
import psutil


@dataclass(frozen=True)
class ProcessRow:
    pid: int
    name: str
    cpu: float | None
    rss: int | None


def cpu_share(previous, current, elapsed, logical_count):
    if previous is None or current is None or elapsed <= 0 or logical_count <= 0:
        return None
    if current < previous:
        return None
    return min(100.0, 100.0 * (current - previous) / elapsed / logical_count)


def filter_sort(rows, query="", key="cpu", descending=True):
    query = query.strip().casefold()
    matched = [row for row in rows if not query or
               query in row.name.casefold() or query in str(row.pid)]
    known = [row for row in matched if getattr(row, key) is not None]
    unknown = [row for row in matched if getattr(row, key) is None]
    known.sort(key=lambda row: row.pid)
    known.sort(key=lambda row: getattr(row, key).casefold() if key == "name"
               else getattr(row, key), reverse=descending)
    return known + sorted(unknown, key=lambda row: row.pid)


class ProcessSampler:
    def __init__(self):
        self.previous = {}
        self.logical_count = psutil.cpu_count() or 1

    def sample(self):
        now = time.monotonic()
        rows = []
        next_previous = {}
        for proc in psutil.process_iter(
            ["pid", "name", "create_time", "cpu_times", "memory_info"],
            ad_value=None,
        ):
            try:
                info = proc.info
                pid = info["pid"]
                name = info["name"] or "(nedostupný název)"
                created = info["create_time"]
                times = info["cpu_times"]
                total = times.user + times.system if times is not None else None
                identity = (pid, created)
                previous = self.previous.get(identity) if created is not None else None
                cpu = cpu_share(previous[1], total, now - previous[0],
                                self.logical_count) if previous else None
                if created is not None and total is not None:
                    next_previous[identity] = (now, total)
                memory = info["memory_info"]
                rows.append(ProcessRow(pid, name, cpu, memory.rss if memory else None))
            except (psutil.NoSuchProcess, psutil.AccessDenied, OSError):
                continue
        self.previous = next_previous
        return tuple(rows)
