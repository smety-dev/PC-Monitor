import unittest
from unittest.mock import patch, Mock
from pc_monitor.core.process_metrics import ProcessRow, ProcessSampler, cpu_share, filter_sort


class ProcessMetricsTests(unittest.TestCase):
    def test_idle_process_excluded(self):
        idle = Mock(info={"pid": 0})
        with patch("pc_monitor.core.process_metrics.psutil.process_iter", return_value=[idle]):
            self.assertEqual(ProcessSampler().sample(), ())

    def test_cpu_share(self):
        self.assertEqual(cpu_share(10, 12, 2, 4), 25)
        self.assertEqual(cpu_share(10, 10, 2, 4), 0)
        self.assertEqual(cpu_share(0, 20, 1, 4), 100)

    def test_missing_or_reset(self):
        for args in ((None, 10, 1, 4), (10, None, 1, 4),
                     (10, 5, 1, 4), (0, 1, 0, 4), (0, 1, 1, 0)):
            self.assertIsNone(cpu_share(*args))

    def test_filter(self):
        rows = [ProcessRow(12, "Game.exe", 10, 100),
                ProcessRow(34, "Browser.exe", 20, 200)]
        self.assertEqual(filter_sort(rows, "GAME"), [rows[0]])
        self.assertEqual(filter_sort(rows, "34"), [rows[1]])

    def test_numeric_sort_and_unknown(self):
        rows = [ProcessRow(1, "A", 2, 100),
                ProcessRow(2, "B", 10, 50),
                ProcessRow(3, "C", None, None)]
        self.assertEqual(filter_sort(rows), [rows[1], rows[0], rows[2]])
        self.assertEqual(filter_sort(rows, key="cpu", descending=False), rows)
        self.assertEqual(filter_sort(rows, key="rss"), rows)


if __name__ == "__main__":
    unittest.main()
