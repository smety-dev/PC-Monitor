import unittest
from pc_monitor.core.hardware_metrics import rates


class RatesTests(unittest.TestCase):
    def test_rates(self):
        self.assertEqual(rates((100, 200), (300, 500), 2), (100, 150))

    def test_missing_and_reset(self):
        self.assertIsNone(rates(None, (1, 2), 1))
        self.assertIsNone(rates((1, 2), None, 1))
        self.assertIsNone(rates((10, 20), (5, 30), 1))
        self.assertIsNone(rates((1, 2), (3, 4), 0))

    def test_idle(self):
        self.assertEqual(rates((100, 200), (100, 200), 1), (0, 0))


if __name__ == "__main__":
    unittest.main()
