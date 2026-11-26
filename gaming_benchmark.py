"""Gaming benchmark recording and analysis, independent of Qt and Windows."""
import csv
import math
import re
import time
from array import array
from concurrent.futures import CancelledError
from dataclasses import dataclass
from heapq import nlargest
from statistics import fmean, median

HEADER = ("elapsed_s", "swap_chain", "frametime_ms")
DURATIONS = (30, 60, 120, 300)
MAX_ROWS = 500_000
MAX_CHAINS = 256
MAX_SECONDS = 300
CHAIN_PATTERN = re.compile(r"[a-zA-Z0-9][a-zA-Z0-9_-]{0,63}")


def valid_frame(chain, ms):
    return bool(CHAIN_PATTERN.fullmatch(chain)) and math.isfinite(ms) and 0 < ms <= 3600000


class BenchmarkRecorder:
    """Exclusive CSV creation; buffered batches, no second capture session."""
    def __init__(self, clock=time.monotonic):
        self.clock = clock
        self.file = None
        self.writer = None
        self.path = None
        self.count = 0
        self.started = 0
        self.duration = 0
        self.origin = None
        self.seen = {}
        self.buffer = []

    @property
    def active(self):
        return self.file is not None

    @property
    def elapsed(self):
        return min(self.duration, max(0, self.clock() - self.started)) if self.active else 0

    def start(self, path, duration):
        if self.active or duration not in DURATIONS:
            raise ValueError("Benchmark již běží nebo má neplatnou délku.")
        file = open(path, "x", encoding="utf-8-sig", newline="")
        try:
            writer = csv.writer(file, delimiter=";")
            writer.writerow(HEADER)
            file.flush()
        except Exception:
            file.close()
            raise
        self.file, self.writer, self.path = file, writer, str(path)
        self.count, self.origin, self.duration = 0, None, duration
        self.seen.clear()
        self.buffer.clear()
        self.started = self.clock()

    def add(self, chain, timestamp, ms, received):
        if not self.active or received - self.started >= self.duration:
            return
        if not valid_frame(chain, ms) or not math.isfinite(timestamp):
            return
        if self.origin is None:
            self.origin = timestamp
        if chain not in self.seen:
            # The first interval can include time before recording began.
            if len(self.seen) < MAX_CHAINS:
                self.seen[chain] = timestamp
            return
        if timestamp <= self.seen[chain]:
            return
        self.seen[chain] = timestamp
        elapsed = timestamp - self.origin
        if not 0 <= elapsed <= self.duration or self.count >= MAX_ROWS:
            return
        self.buffer.append((format(elapsed, ".17g").replace(".", ","), chain,
                            format(ms, ".17g").replace(".", ",")))
        self.count += 1
        if len(self.buffer) >= 256:
            self.write_buffer()

    def write_buffer(self):
        if self.active and self.buffer:
            self.writer.writerows(self.buffer)
            self.buffer.clear()

    def flush(self):
        if self.active:
            self.write_buffer()
            self.file.flush()

    def stop(self):
        if self.active:
            file = self.file
            try:
                self.flush()
            finally:
                self.file, self.writer = None, None
                self.buffer.clear()
                file.close()


@dataclass(frozen=True)
class BenchmarkResult:
    chain: str
    chains: int
    count: int
    total_count: int
    span: float
    fps: float
    low: float | None
    average_ms: float
    median_ms: float
    peak_ms: float
    stutters: int
    threshold_ms: float
    severe: int
    fps_series: tuple
    peak_series: tuple

    @property
    def stutter_percent(self):
        return 100 * self.stutters / self.count

    @property
    def severe_percent(self):
        return 100 * self.severe / self.count


def relative_change(baseline, comparison):
    """Percentage change relative to A; a zero baseline cannot define a change."""
    if baseline is None or comparison is None or baseline == 0:
        return None
    return (comparison - baseline) / baseline * 100


def check_cancel(cancel):
    if cancel is not None and cancel.is_set():
        raise CancelledError()


def parse_number(value):
    return float(value.replace(",", "."))


def analyze_benchmark(path, cancel=None):
    """Select one dominant swap chain; do not combine unrelated presents."""
    check_cancel(cancel)
    chains = {}
    total = 0
    with open(path, encoding="utf-8-sig", newline="") as file:
        reader = csv.reader(file, delimiter=";")
        if tuple(next(reader, ())) != HEADER:
            raise ValueError("Soubor není benchmark CSV z PC Monitoru.")
        for i, row in enumerate(reader):
            if i % 1024 == 0:
                check_cancel(cancel)
            if i >= MAX_ROWS:
                raise ValueError("Benchmark překročil limit 500 000 snímků.")
            if len(row) != 3:
                raise ValueError("Neplatný řádek benchmarku.")
            try:
                t, chain, ms = parse_number(row[0]), row[1], parse_number(row[2])
            except ValueError as exc:
                raise ValueError("Neplatné číselné hodnoty benchmarku.") from exc
            if not math.isfinite(t) or not 0 <= t <= MAX_SECONDS or not valid_frame(chain, ms):
                raise ValueError("Neplatný frametime nebo čas benchmarku.")
            if chain not in chains:
                if len(chains) >= MAX_CHAINS:
                    raise ValueError("Příliš mnoho swap chainů.")
                chains[chain] = (array("d"), array("d"))
            times, values = chains[chain]
            if times and t <= times[-1]:
                raise ValueError("Čas snímků není rostoucí.")
            times.append(t)
            values.append(ms)
            total += 1
    if not total:
        raise ValueError("Benchmark neobsahuje žádné snímky.")
    chain = max(chains, key=lambda key: len(chains[key][0]))
    times, values = chains[chain]
    count = len(values)
    check_cancel(cancel)
    mean = fmean(values)
    typical = median(values)
    threshold = max(33.333, 2 * typical)
    low = 1000 / fmean(nlargest(math.ceil(count * .01), values)) if count >= 100 else None
    sums = [0.0] * (int(times[-1]) + 1)
    counts = [0] * len(sums)
    peaks = [None] * len(sums)
    stutters = severe = 0
    for i, (t, ms) in enumerate(zip(times, values)):
        if i % 1024 == 0:
            check_cancel(cancel)
        second = int(t)
        sums[second] += ms
        counts[second] += 1
        peaks[second] = ms if peaks[second] is None else max(peaks[second], ms)
        stutters += ms >= threshold
        severe += ms >= 50
    fps = tuple(1000 * n / s if n else None for n, s in zip(counts, sums))
    return BenchmarkResult(chain, len(chains), count, total, times[-1] - times[0],
                           1000 / mean, low, mean, typical, max(values),
                           stutters, threshold, severe, fps, tuple(peaks))


def create_demo(path, improved=False):
    """Create clearly synthetic samples for testing the analyzer without ETW."""
    with open(path, "x", encoding="utf-8-sig", newline="") as file:
        writer = csv.writer(file, delimiter=";")
        writer.writerow(HEADER)
        elapsed = 0.0
        index = 0
        while elapsed < 30:
            ms = (11.5 if improved else 16.5) + (index % 9 - 4) * 0.25
            if index % (240 if improved else 90) == 45:
                ms = 45.0 if improved else 85.0
            elapsed += ms / 1000
            if elapsed <= 30:
                writer.writerow((format(elapsed, ".9f").replace(".", ","), "demo", str(ms).replace(".", ",")))
            index += 1


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Create synthetic benchmark CSV files for UI testing")
    parser.add_argument("--demo", action="store_true", required=True)
    parser.parse_args()
    for name, improved in (("A", False), ("B", True)):
        path = f"pc-monitor-benchmark-demo-{name}.csv"
        try:
            create_demo(path, improved)
            print("Created synthetic demo:", path)
        except FileExistsError:
            print("Existing file preserved:", path)
