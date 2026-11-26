import csv
import tempfile
import unittest
from pathlib import Path
from performance_logger import FIELDS, CSV_HEADERS
from performance_analysis import read_recording, summarize, utilization_hints, number


class AnalysisTests(unittest.TestCase):
    def load(self, headers, rows):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "record.csv"
            with path.open("w", encoding="utf-8-sig", newline="") as file:
                writer = csv.writer(file, delimiter=";")
                writer.writerow(headers)
                writer.writerows(rows)
            return read_recording(path)

    def test_czech_and_statistics(self):
        rows, skipped = self.load(CSV_HEADERS, [
            ["26.11.2026", "0,5", "8,8", "80", "1000", "", "3000", "", "", "", ""],
            ["26.11.2026", "1,5", "11,2", "82", "900", "95", "3000", "", "", "", ""],
        ])
        self.assertEqual(skipped, 0)
        self.assertEqual(summarize(rows)["cpu_percent"], (8.8, 10.0, 11.2, 2))
        self.assertEqual(summarize(rows)["gpu_3d_percent"], (95, 95, 95, 1))
        self.assertIsNone(summarize(rows)["disk_read_mib_s"])

    def test_old_format(self):
        rows, _ = self.load(FIELDS, [["timestamp", "0.5", "20.1", "", "", "", "", "", "", "", ""]])
        self.assertEqual(rows[0]["cpu_percent"], 20.1)

    def test_invalid_values_and_rows(self):
        rows, skipped = self.load(FIELDS, [
            ["", "1", "NaN", "-1", "", "", "", "", "", "", ""],
            ["", "0", "20", "", "", "", "", "", "", "", ""],
            ["", "bad", "20", "", "", "", "", "", "", "", ""],
        ])
        self.assertEqual(skipped, 2)
        self.assertIsNone(rows[0]["cpu_percent"])
        self.assertIsNone(rows[0]["ram_percent"])
        self.assertIsNone(number("inf"))

    def test_invalid_header(self):
        with self.assertRaises(ValueError):
            self.load(["other"], [["value"]])

    def test_empty_recording(self):
        with self.assertRaises(ValueError):
            self.load(FIELDS, [])

    def test_hints(self):
        rows, _ = self.load(FIELDS, [
            ["", str(i), "10", "60", "1000", "98", "", "", "", "", ""]
            for i in range(6)
        ])
        self.assertTrue(utilization_hints(rows, summarize(rows))[0].startswith("GPU 3D"))
        self.assertIn("nikoli důkaz", utilization_hints(rows, summarize(rows))[-1])


if __name__ == "__main__":
    unittest.main()
