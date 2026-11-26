"""GUI smoke tests with synthetic data and no capture or hardware workers."""
import os
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory
from threading import Event
from types import SimpleNamespace
from unittest.mock import Mock, patch

# Offscreen rendering needs no visible desktop, Windows ETW or admin rights.
os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
from PySide6.QtCore import QSettings, QSize
from PySide6.QtGui import QIcon
from PySide6.QtWidgets import QApplication

from gaming_benchmark import analyze_benchmark, create_demo
from preferences import Preferences, PAGES
from i18n import set_language
from qt_gui import Window
from qt_pages import configure_chart_fonts
from qt_theme import configure_theme, navigation_icon, NAV_ICONS, preferred_font


class UISmokeTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication([])
        configure_chart_fonts(configure_theme(cls.app))

    def setUp(self):
        folder = TemporaryDirectory()
        self.addCleanup(folder.cleanup)
        self.folder = Path(folder.name)
        prefs = Preferences(QSettings(str(self.folder / "test.ini"), QSettings.Format.IniFormat))
        prefs.set("ui/language", "cs")
        self.prefs = prefs
        self.addCleanup(set_language, "cs")
        monitor = Mock()
        monitor.basic = (12.5, SimpleNamespace(percent=40.0, total=16*1024**3, available=9.6*1024**3))
        monitor.gpu = 8.0
        monitor.gpu_names = ("Synthetic GPU",)
        monitor.hardware = "Synthetic CPU · Synthetic GPU"
        monitor.advanced = {"frequency": 3600, "cores": [12.5, 18.0],
                            "disk_rates": (1024**2, 2*1024**2),
                            "net_rates": (3*1024**2, 4*1024**2),
                            "drives": [("C:", 20*1024**3, 100*1024**3, 20)]}
        monitor.processes = []
        monitor.gaming = Event()
        self.monitor = monitor
        with patch("qt_gui.Monitor", return_value=monitor), patch("qt_gui.Preferences", return_value=prefs):
            self.window = Window()
        self.window.timer.stop()
        self.addCleanup(self.close_window)
        self.window.show()
        self.app.processEvents()

    def close_window(self):
        self.window.close()
        self.window.deleteLater()
        self.app.processEvents()

    def test_all_pages_and_tabs(self):
        self.assertEqual(tuple(view[0] for view in self.window.views), PAGES)
        for i in range(len(PAGES)):
            self.window.navigate(i)
            self.window.refresh()
            self.app.processEvents()
            self.assertEqual(self.window.stack.currentIndex(), i)
            self.assertTrue(self.window.group.button(i).isChecked())
        self.window.open_fps()
        self.assertEqual(self.window.gaming.tabs.currentIndex(), 0)
        self.window.open_overlay()
        self.assertEqual(self.window.gaming.tabs.currentIndex(), 1)
        self.assertEqual(self.window.benchmark.tabs.count(), 3)

    def test_english_workspace(self):
        self.close_window()
        self.prefs.set("ui/language", "en")
        with patch("qt_gui.Monitor", return_value=self.monitor):
            self.window = Window(prefs=self.prefs)
        self.window.timer.stop()
        self.window.show()
        self.window.navigate(0)
        self.window.refresh()
        self.assertEqual(self.window.title.text(), "System overview")
        self.assertEqual(self.window.group.button(0).text(), "Overview")
        self.assertEqual(self.window.metrics[0].value.text(), "12.5")
        self.assertEqual(self.window.activity_values[0].text(), "1.00 MiB/s")
        self.assertEqual(self.window.gaming.corner.currentData(), self.prefs.get("overlay/corner"))
        self.assertEqual(self.window.gaming.corner.currentText(), "Top right")
        self.assertEqual(self.window.gaming.tabs.tabText(0), "FPS capture")
        self.assertEqual(self.window.benchmark.tabs.tabText(1), "A/B results")
        self.assertEqual(self.window.analysis.group.itemText(0), "Utilization (%)")
        self.assertEqual(self.window.analysis.group.currentData(), "Vytížení (%)")
        page = self.window.benchmark
        for i, improved in enumerate((False, True)):
            path = self.folder / f"english-{i}.csv"
            create_demo(path, improved)
            page.results[i] = analyze_benchmark(path)
        page.render()
        self.assertIn("Average FPS", page.comparison_summary.text())
        self.assertEqual(page.t.item(0, 0).text(), "Average FPS")
        self.assertEqual(self.window.plot.ax.xaxis.get_major_formatter()(0), "Now")
        for index in range(len(PAGES)):
            self.window.navigate(index)
            self.window.refresh()
        self.assertEqual(self.prefs.get("startup/last_page"), "Nastavení")
        self.assertEqual(self.window.title.text(), "Application settings")
        self.window.settings_page.language.setCurrentIndex(
            self.window.settings_page.language.findData("cs"))
        self.assertEqual(self.prefs.get("ui/language"), "cs")
        self.assertEqual(self.window.title.text(), "Application settings")

    def test_overview_values(self):
        self.window.navigate(0)
        self.window.refresh()
        self.assertEqual(self.window.metrics[0].value.text(), "12,5")
        self.assertEqual(self.window.metrics[1].bar.value(), 400)
        self.assertEqual(self.window.metrics[2].detail.text(), "Synthetic GPU")
        self.assertEqual(self.window.activity_values[0].text(), "1,00 MiB/s")
        self.assertEqual(self.window.activity_values[3].text(), "4,00 MiB/s")

    def test_benchmark_comparison(self):
        page = self.window.benchmark
        for i, improved in enumerate((False, True)):
            path = self.folder / f"sample-{i}.csv"
            create_demo(path, improved)
            page.results[i] = analyze_benchmark(path)
        page.render()
        self.assertGreater(page.results[1].fps, page.results[0].fps)
        self.assertIn("FPS", page.comparison_summary.text())
        self.assertEqual(page.t.rowCount(), 12)
        self.assertEqual(len(page.fps_plot.ax.lines), 2)
        self.assertEqual(len(page.peak_plot.ax.lines), 2)

    def test_icon_states_and_font_fallback(self):
        self.assertEqual(preferred_font(["Segoe UI", "Inter"]), "Segoe UI")
        self.assertEqual(preferred_font([]), "Sans Serif")
        for name in NAV_ICONS:
            icon = navigation_icon(name)
            reference = icon.pixmap(QSize(20, 20), QIcon.Mode.Normal, QIcon.State.Off).toImage()
            self.assertFalse(reference.isNull())
            for mode in (QIcon.Mode.Normal, QIcon.Mode.Active, QIcon.Mode.Selected, QIcon.Mode.Disabled):
                for state in (QIcon.State.Off, QIcon.State.On):
                    self.assertEqual(reference, icon.pixmap(QSize(20, 20), mode, state).toImage())

    def test_history_filter_and_time_axis(self):
        window = self.window
        window.navigate(0)
        window.history.clear()
        window.history.extend(((100.0, 10.0, 40.0, 8.0),
                               (101.0, 12.0, 41.0, 9.0),
                               (106.0, 14.0, 42.0, None)))
        window.history_filter.setCurrentIndex(0)
        window.render_page()
        self.assertEqual(tuple(window.plot.ax.get_xlim()), (-60.0, 0.0))
        self.assertEqual(list(window.plot.ax.get_yticks()), [0, 25, 50, 75, 100])
        self.assertEqual(len(window.plot.ax.lines), 3)
        self.assertEqual(list(window.plot.ax.lines[0].get_xdata()), [-6.0, -5.0, -2.5, 0.0])
        import math
        self.assertTrue(math.isnan(window.plot.ax.lines[0].get_ydata()[2]))
        window.history_filter.setCurrentIndex(2)
        self.assertEqual(len(window.plot.ax.lines), 1)
        self.assertEqual(window.plot.ax.lines[0].get_label(), "RAM")
        self.assertEqual(window.plot.ax.lines[0].get_ydata()[-1], 42.0)

    def test_product_icon(self):
        import struct
        from app_identity import SIZES, app_icon, write_ico
        target = self.folder / "test.ico"
        write_ico(target)
        raw = target.read_bytes()
        self.assertEqual(struct.unpack_from("<HHH", raw), (0, 1, len(SIZES)))
        for i, size in enumerate(SIZES):
            width, height, _, _, _, bits, length, offset = struct.unpack_from("<BBBBHHII", raw, 6 + i * 16)
            self.assertEqual((width or 256, height or 256, bits), (size, size, 32))
            self.assertEqual(raw[offset:offset+8], b"\x89PNG\r\n\x1a\n")
            self.assertLessEqual(offset + length, len(raw))
        self.assertFalse(app_icon().isNull())
