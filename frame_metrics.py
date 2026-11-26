"""PresentMon 2.3.1 legacy CSV metrics, independent of Qt and Windows."""
import csv
import math
from heapq import nlargest
from collections import deque
from dataclasses import dataclass
from statistics import fmean

WINDOW_SECONDS = 10
MAX_FRAMES = 12000
MAX_CHAINS = 16


@dataclass(frozen=True)
class FrameStats:
    fps: float
    average_fps: float
    frametime: float
    low: float | None
    count: int
    chain: str
    graph: tuple


class FrameStream:
    def __init__(self, pid):
        self.pid = pid
        self.header = None
        self.chains = {}
        self.latest = None
        self.last_received = None
        self.cached = None

    def feed(self, line, received):
        try:
            cells = next(csv.reader([line.strip().lstrip("\ufeff")]))
        except (csv.Error, StopIteration):
            return False
        if "MsBetweenPresents" in cells and "ProcessID" in cells:
            self.header = {name: i for i, name in enumerate(cells)}
            return False
        if self.header is None:
            return False
        try:
            def field(name):
                return cells[self.header[name]]
            if int(field("ProcessID")) != self.pid:
                return False
            chain = field("SwapChainAddress")
            timestamp = float(field("TimeInSeconds"))
            ms = float(field("MsBetweenPresents"))
        except (ValueError, KeyError, IndexError):
            return False
        if not chain or not math.isfinite(timestamp) or not math.isfinite(ms) or timestamp < 0 or ms <= 0:
            return False
        if chain not in self.chains:
            if len(self.chains) >= MAX_CHAINS:
                oldest = min(self.chains, key=lambda key: self.chains[key][-1][0] if self.chains[key] else -1)
                del self.chains[oldest]
            self.chains[chain] = deque(maxlen=MAX_FRAMES)
        frames = self.chains[chain]
        if frames and timestamp <= frames[-1][0]:
            return False
        frames.append((timestamp, ms))
        self.latest = timestamp if self.latest is None else max(self.latest, timestamp)
        self.last_received = received
        self.cached = None
        return True

    def snapshot(self, now):
        if self.latest is None or now - self.last_received > 3:
            return None
        if self.cached is not None:
            return self.cached
        recent = {}
        for key, frames in self.chains.items():
            while frames and frames[0][0] < self.latest - WINDOW_SECONDS:
                frames.popleft()
            if frames:
                recent[key] = sum(t >= self.latest - 2 for t, _ in frames)
        if not recent or max(recent.values()) == 0:
            return None
        chain = max(recent, key=recent.get)
        frames = self.chains[chain]
        values = [ms for _, ms in frames]
        current = [ms for t, ms in frames if t >= self.latest - 1]
        if not current:
            return None
        mean = fmean(current)
        low = None
        if len(values) >= 100:
            slowest = nlargest(math.ceil(len(values)*.01), values)
            low = 1000 / fmean(slowest)
        self.cached = FrameStats(1000 / mean, 1000 / fmean(values), mean, low,
                                 len(values), chain, tuple(values[-120:]))
        return self.cached
