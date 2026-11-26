import csv
import tempfile
import unittest
from concurrent.futures import CancelledError
from pathlib import Path
from threading import Event
from unittest.mock import Mock, patch
from gaming_benchmark import BenchmarkRecorder, HEADER, analyze_benchmark


class BenchmarkTests(unittest.TestCase):
    def setUp(self):
        self.folder = tempfile.TemporaryDirectory()
        self.addCleanup(self.folder.cleanup)
        self.path = Path(self.folder.name) / "bench.csv"

    def write(self, rows, header=HEADER):
        with self.path.open("w", encoding="utf-8-sig", newline="") as file:
            writer = csv.writer(file, delimiter=";")
            writer.writerow(header)
            writer.writerows(rows)

    def test_record_roundtrip(self):
        recorder = BenchmarkRecorder(Mock(return_value=100))
        recorder.start(self.path, 30)
        self.addCleanup(recorder.stop)
        recorder.add("a", 1, 900, 100)
        for i in range(1, 121):
            recorder.add("a", 1+i/60, 1000/60, 102)
        recorder.stop()
        self.assertFalse(recorder.active)
        result = analyze_benchmark(self.path)
        self.assertEqual(result.count, 120)
        self.assertAlmostEqual(result.fps, 60)
        self.assertAlmostEqual(result.low, 60)
        self.assertEqual(result.stutters, 0)

    def test_duration_and_duplicate(self):
        recorder = BenchmarkRecorder(Mock(return_value=0))
        recorder.start(self.path, 30)
        self.addCleanup(recorder.stop)
        recorder.add("a", 1, 10, 0)
        recorder.add("a", 2, 10, 1)
        recorder.add("a", 2, 10, 2)
        recorder.add("a", 3, 10, 30)
        recorder.stop()
        self.assertEqual(analyze_benchmark(self.path).count, 1)

    def test_exclusive_file(self):
        self.path.write_text("keep", encoding="utf-8")
        with self.assertRaises(FileExistsError):
            BenchmarkRecorder().start(self.path, 30)
        self.assertEqual(self.path.read_text(encoding="utf-8"), "keep")

    def test_invalid_duration(self):
        with self.assertRaises(ValueError):
            BenchmarkRecorder().start(self.path, 10)
        self.assertFalse(self.path.exists())

    def test_stutters_and_low(self):
        self.write([(i*.01, "a", 100 if i == 50 else 10) for i in range(100)])
        result = analyze_benchmark(self.path)
        self.assertAlmostEqual(result.low, 10)
        self.assertEqual(result.stutters, 1)
        self.assertEqual(result.severe, 1)
        self.assertEqual(result.stutter_percent, 1)
        self.assertEqual(result.severe_percent, 1)
        self.assertEqual(max(result.peak_series), 100)

    def test_dominant_chain(self):
        self.write([(i*.02, "a", 20) for i in range(50)] +
                   [(i*.1, "b", 100) for i in range(10)])
        result = analyze_benchmark(self.path)
        self.assertEqual(result.chain, "a")
        self.assertEqual(result.total_count, 60)
        self.assertEqual(result.count, 50)
        self.assertEqual(result.fps, 50)
        self.assertIsNone(result.low)

    def test_gap_retained(self):
        self.write([(0, "a", "16,5"), (2, "a", "70")])
        result = analyze_benchmark(self.path)
        self.assertIsNone(result.fps_series[1])
        self.assertEqual(result.peak_series, (16.5, None, 70.0))

    def test_import_validation(self):
        for rows, header in (([], HEADER), ([(1, "a", "nan")], HEADER),
                             ([(1, "a", 0)], HEADER), ([(301, "a", 1)], HEADER),
                             ([(1, "a", 1), (1, "a", 2)], HEADER),
                             ([(1, "a", 1)], ("other",))):
            with self.subTest(rows=rows, header=header):
                self.write(rows, header)
                with self.assertRaises(ValueError):
                    analyze_benchmark(self.path)

    def test_import_limit_and_cancellation(self):
        self.write([(0, "a", 10), (1, "a", 10)])
        with patch("gaming_benchmark.MAX_ROWS", 1):
            with self.assertRaises(ValueError):
                analyze_benchmark(self.path)
        cancel = Event()
        cancel.set()
        with self.assertRaises(CancelledError):
            analyze_benchmark(self.path, cancel)
