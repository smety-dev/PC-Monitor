import csv
import tempfile
import unittest
from pathlib import Path
from performance_logger import PerformanceRecorder, FIELDS, make_row


class RecordingTests(unittest.TestCase):
    def test_units_and_missing(self):
        row = make_row(1, 20, 30, 1048576, None,
                       {"disk_rates": (2097152, 0)}, "test")
        self.assertEqual(row["ram_available_mib"], 1)
        self.assertEqual(row["disk_read_mib_s"], 2)
        self.assertEqual(row["disk_write_mib_s"], 0)
        self.assertIsNone(row["gpu_3d_percent"])
        self.assertIsNone(row["net_receive_mib_s"])

    def test_interval_and_csv(self):
        now = [0.0]
        rec = PerformanceRecorder(clock=lambda: now[0])
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "test.csv"
            rec.start(path, 2)
            try:
                self.assertTrue(rec.record(10, 20, 1048576, None, None))
                now[0] = 1
                self.assertFalse(rec.record(10, 20, 1048576, None, None))
                now[0] = 5
                self.assertTrue(rec.record(10, 20, 1048576, 30, None))
                self.assertFalse(rec.record(10, 20, 1048576, 30, None))
                self.assertEqual(rec.count, 2)
            finally:
                rec.stop()
            with path.open(encoding="utf-8-sig", newline="") as file:
                reader = csv.DictReader(file, delimiter=";")
                self.assertEqual(tuple(reader.fieldnames), FIELDS)
                rows = list(reader)
            self.assertEqual(len(rows), 2)
            self.assertEqual(rows[0]["gpu_3d_percent"], "")
            self.assertEqual(float(rows[1]["elapsed_s"]), 5)
            self.assertFalse(rec.active)
            self.assertFalse(rec.record(10, 20, 0, None, None))

    def test_no_overwrite(self):
        rec = PerformanceRecorder()
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "existing.csv"
            path.write_text("keep")
            with self.assertRaises(FileExistsError):
                rec.start(path)
            self.assertEqual(path.read_text(), "keep")
            self.assertFalse(rec.active)

    def test_invalid_interval(self):
        rec = PerformanceRecorder()
        with self.assertRaises(ValueError):
            rec.start("unused.csv", 3)


if __name__ == "__main__":
    unittest.main()
