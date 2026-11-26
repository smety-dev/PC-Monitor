"""Regression tests for performance and stability helpers."""
import unittest
from concurrent.futures import CancelledError
from threading import Event
from types import SimpleNamespace
from unittest.mock import patch, Mock

from qt_monitor import Monitor, gpu_value
from hardware_metrics import Sampler
from frame_metrics import FrameStream
from performance_analysis import read_recording, summarize, utilization_hints


class StabilityTests(unittest.TestCase):
    def test_gpu_values(self):
        self.assertEqual(gpu_value("23,45"), 23.4)
        self.assertEqual(gpu_value("105"), 100)
        for raw in ("", "N/A", "-1", "inf", "nan"):
            self.assertIsNone(gpu_value(raw))

    def test_gpu_stale(self):
        monitor = Monitor()
        monitor._gpu_sample = (42.0, 100.0)
        with patch("qt_monitor.time.monotonic", return_value=107):
            self.assertEqual(monitor.gpu, 42)
        with patch("qt_monitor.time.monotonic", return_value=109):
            self.assertIsNone(monitor.gpu)

    def test_hidden_process_state(self):
        monitor = Monitor()
        monitor.set_process_visible(True)
        self.assertTrue(monitor.process_visible.is_set())
        monitor.processes = ("sample",)
        monitor.set_process_visible(False)
        self.assertFalse(monitor.process_visible.is_set())
        self.assertIsNone(monitor.processes)
        monitor.set_gaming(True)
        self.assertTrue(monitor.gaming.is_set())

    def test_close_terminates_tracked_children(self):
        monitor = Monitor()
        child = Mock()
        monitor.children.add(child)
        monitor.close()
        self.assertTrue(monitor.stop_event.is_set())
        child.terminate.assert_called_once()
        child.kill.assert_called_once()

    def test_drive_capacity_cache(self):
        clock = Mock(side_effect=[0, 1, 10])
        usage = SimpleNamespace(used=10, total=20, percent=50)
        partition = SimpleNamespace(opts="", mountpoint="test")
        with patch("hardware_metrics.psutil.disk_partitions", return_value=[partition]) as partitions, \
             patch("hardware_metrics.psutil.disk_usage", return_value=usage) as disk_usage, \
             patch("hardware_metrics.psutil.disk_io_counters", return_value=None), \
             patch("hardware_metrics.psutil.net_io_counters", return_value=None), \
             patch("hardware_metrics.psutil.cpu_freq", return_value=None), \
             patch("hardware_metrics.psutil.cpu_percent", return_value=[]):
            sampler = Sampler(clock)
            a, b, c = (sampler.sample() for _ in range(3))
        self.assertEqual(partitions.call_count, 2)
        self.assertEqual(disk_usage.call_count, 2)
        self.assertEqual(a["drives"], b["drives"])
        self.assertEqual(c["drives"], [("test", 10, 20, 50)])

    def test_frame_cache_and_expiry(self):
        stream = FrameStream(42)
        stream.feed("ProcessID,SwapChainAddress,TimeInSeconds,MsBetweenPresents", 0)
        stream.feed("42,a,1,20", 1)
        first = stream.snapshot(1)
        self.assertIsNotNone(first)
        self.assertIs(stream.snapshot(2), first)
        stream.feed("42,a,1.01,10", 2)
        self.assertIsNot(stream.snapshot(2), first)
        self.assertIsNone(stream.snapshot(6))

    def test_analysis_cancelled(self):
        cancel = Event()
        cancel.set()
        with self.assertRaises(CancelledError):
            read_recording("unused.csv", cancel)
        with self.assertRaises(CancelledError):
            summarize([], cancel)
        with self.assertRaises(CancelledError):
            utilization_hints([], {}, cancel)
