"""Unit tests for overlay helpers, independent of Qt."""
import unittest
from gaming_metrics import CORNERS, percent, fraction, frequency, available_memory, overlay_position


class GamingMetricsTests(unittest.TestCase):
    def test_missing_metrics(self):
        for value in (None, float("nan"), float("inf"), -1):
            self.assertEqual(percent(value), "N/A")
            self.assertEqual(fraction(value), 0)
            self.assertEqual(frequency(value), "N/A")
            self.assertEqual(available_memory(value), "N/A")

    def test_percent_and_progress(self):
        self.assertEqual(percent(67.4), "67 %")
        self.assertAlmostEqual(fraction(67.4), .674)
        self.assertEqual(fraction(120), 1)
        self.assertEqual(percent(0), "0 %")

    def test_units(self):
        self.assertEqual(frequency(3000), "3.00 GHz")
        self.assertEqual(available_memory(2 * 1024**3), "2.0 GiB volné")

    def test_corners(self):
        screen = (0, 0, 1920, 1080)
        size = (310, 166)
        self.assertEqual([overlay_position(screen, size, corner) for corner in CORNERS],
                         [(16,16), (1594,16), (16,898), (1594,898)])

    def test_negative_monitor_coordinates(self):
        self.assertEqual(overlay_position((-1920, -100, 1920, 1080), (310,166), CORNERS[1]),
                         (-326,-84))

    def test_small_screen_and_invalid_corner(self):
        self.assertEqual(overlay_position((5,7,100,80), (310,166), CORNERS[3]), (5,7))
        with self.assertRaises(ValueError):
            overlay_position((0,0,1920,1080), (310,166), "invalid")
