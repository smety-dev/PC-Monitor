import unittest
from frame_metrics import FrameStream


HEADER = "Application,ProcessID,SwapChainAddress,Runtime,TimeInSeconds,MsBetweenPresents"


class FrameMetricsTests(unittest.TestCase):
    def stream(self):
        s = FrameStream(42)
        s.feed(HEADER, 0)
        return s

    def test_constant_fps(self):
        s = self.stream()
        for i in range(120):
            s.feed(f"game.exe,42,0x1,DXGI,{i/60},16.6666666667", 1)
        stats = s.snapshot(1)
        self.assertAlmostEqual(stats.fps, 60, places=4)
        self.assertAlmostEqual(stats.average_fps, 60, places=4)
        self.assertAlmostEqual(stats.low, 60, places=4)
        self.assertEqual(stats.count, 120)

    def test_one_percent_low(self):
        s = self.stream()
        for i in range(100):
            s.feed(f"game.exe,42,a,DXGI,{i*.01},{100 if i==50 else 10}", 1)
        self.assertAlmostEqual(s.snapshot(1).low, 10)

    def test_invalid_and_wrong_process(self):
        s = self.stream()
        for row in ("game.exe,99,a,DXGI,1,10", "game.exe,42,a,DXGI,1,0",
                    "game.exe,42,a,DXGI,1,NaN", "game.exe,42,a,DXGI,1,NA",
                    "game.exe,42,a,DXGI,bad,10", "bad"):
            self.assertFalse(s.feed(row, 1))
        self.assertIsNone(s.snapshot(1))

    def test_stale_and_small_sample(self):
        s = self.stream()
        s.feed("game.exe,42,a,DXGI,1,20", 1)
        self.assertIsNone(s.snapshot(1).low)
        self.assertIsNone(s.snapshot(5))

    def test_dominant_swap_chain(self):
        s = self.stream()
        for i in range(60):
            s.feed(f"game.exe,42,a,DXGI,{i/60},16.6666667", 1)
            if i % 10 == 0:
                s.feed(f"game.exe,42,b,DXGI,{i/60},100", 1)
        self.assertEqual(s.snapshot(1).chain, "a")
        self.assertAlmostEqual(s.snapshot(1).fps, 60, places=3)

    def test_rolling_window(self):
        s = self.stream()
        for i in range(20):
            s.feed(f"game.exe,42,a,DXGI,{i},1000", i)
        self.assertEqual(s.snapshot(19).count, 11)
        self.assertEqual(s.snapshot(19).fps, 1)

    def test_duplicate_timestamp(self):
        s = self.stream()
        self.assertTrue(s.feed("game.exe,42,a,DXGI,1,20", 1))
        self.assertFalse(s.feed("game.exe,42,a,DXGI,1,30", 1))
        self.assertEqual(s.snapshot(1).count, 1)
